#!/usr/bin/env python3
"""Read-only, offline readiness checks for setup, search, ranking and applications.

This checks local prerequisites, not portal availability or PDF compilation.
It never runs install/build commands, fetches jobs, or prints candidate values.
Exit 1 means a prerequisite for the selected scope needs attention; warnings
(optional tools, unverified custom toolchains) do not block the workflow.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROFILE_DIR = Path(".claude/skills/job-application-assistant")
PLACEHOLDER = re.compile(r"\[[A-Z][A-Z_0-9]*(?:,[^\]\n]*)?\]")
SCOPES = ("setup", "profile", "search", "apply", "all")


def check(checks: list[dict], name: str, status: str, message: str, fix: str = "") -> None:
    row = {"name": name, "status": status, "message": message}
    if fix:
        row["fix"] = fix
    checks.append(row)


def read_local(root: Path, relative: Path | str, checks: list[dict]) -> str | None:
    """Report missing/unreadable input without leaking its contents."""
    label = Path(relative).as_posix()
    try:
        return (root / relative).read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError):
        check(checks, label, "error", "Required file is missing or unreadable.",
              "Restore this file from the framework before continuing.")
        return None


def without_comments(text: str) -> str:
    return re.sub(r"<!--.*?-->", "", text, flags=re.S)


def section(text: str, heading: str) -> str:
    match = re.search(rf"^(#{{1,6}}) {re.escape(heading)}[^\S\n]*\n", text, re.M)
    if not match:
        return ""
    body = text[match.end():]
    next_heading = re.search(rf"^#{{1,{len(match.group(1))}}} ", body, re.M)
    return body[:next_heading.start()] if next_heading else body


def initialized(value: str) -> bool:
    return bool(value.strip()) and not PLACEHOLDER.search(value)


def languages_ready(text: str) -> bool:
    """Require a declared language AND level, not just the table headings."""
    in_table = False
    for line in text.splitlines():
        if re.match(r"\s*\|\s*Language\s*\|\s*Level\s*\|", line, re.I):
            in_table = True
            continue
        if not in_table:
            continue
        if not line.strip().startswith("|"):
            in_table = False
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 2 or all(re.fullmatch(r"[:\- ]*", c) for c in cells):
            continue
        if initialized(cells[0]) and initialized(cells[1]):
            return True
    return False


def profile_checks(root: Path, checks: list[dict]) -> None:
    for relative in (Path("CLAUDE.md"), PROFILE_DIR / "01-candidate-profile.md"):
        text = read_local(root, relative, checks)
        if text is None:
            continue
        text = without_comments(text)
        missing = []
        for field in ("Name", "Location"):
            match = re.search(rf"^[ \t]*-[ \t]*\*\*{field}:\*\*[ \t]*([^\r\n]*)$", text, re.M)
            if not match or not initialized(match.group(1)):
                missing.append(field.lower())
        if not languages_ready(text):
            missing.append("working languages and levels")
        skills = section(text, "Technical Skills")
        if not any(initialized(line.lstrip("- ")) for line in skills.splitlines()
                   if line.strip().startswith("-")):
            missing.append("skills")
        if relative.name == "CLAUDE.md":
            match = re.search(r"^[ \t]*-[ \t]*\*\*CV language:\*\*[ \t]*([^\r\n]*)$", text, re.M)
            if not match or not initialized(match.group(1)):
                missing.append("CV language")
        label = relative.as_posix()
        if missing:
            check(checks, f"profile:{label}", "error",
                  "Not initialized: " + ", ".join(missing) + ".",
                  "Run the canonical .claude/commands/setup.md workflow (/setup).")
        else:
            check(checks, f"profile:{label}", "ok", "Essential profile fields are filled in.")


def enabled_portal(text: str) -> bool:
    """Missing enabled defaults to true, matching /scrape's discovery contract."""
    frontmatter = re.match(r"\A---\s*\n(.*?)\n---", text, re.S)
    if not frontmatter:
        raise ValueError("missing frontmatter")
    match = re.search(r"^enabled:\s*([^\n#]+)", frontmatter.group(1), re.M)
    if not match:
        return True
    value = match.group(1).strip().strip("\"'").lower()
    if value not in ("true", "false"):
        raise ValueError("enabled must be true or false")
    return value == "true"


def search_checks(root: Path, checks: list[dict]) -> None:
    bun = shutil.which("bun")
    check(checks, "bun", "ok" if bun else "warning",
          "Bun is available on PATH." if bun else "Bun is missing from PATH.",
          "Install Bun using SETUP.md, or use the canonical WebSearch fallback." if not bun else "")
    skills = root / ".agents/skills"
    enabled = 0
    for skill in sorted(skills.glob("*/SKILL.md")):
        # Agent Skills also contains workflow routers. A CLI sibling identifies
        # a portal candidate; keep incomplete CLIs in the checks so damage is
        # reported rather than silently hiding the portal from discovery.
        cli = skill.parent / "cli"
        if not cli.exists():
            continue
        relative = skill.relative_to(root)
        text = read_local(root, relative, checks)
        if text is None:
            continue
        try:
            active = enabled_portal(text)
        except ValueError:
            check(checks, f"portal:{skill.parent.name}", "error", "Invalid portal frontmatter.",
                  "Use a YAML frontmatter block with enabled: true or false.")
            continue
        if not active:
            continue
        enabled += 1
        manifest = read_local(root, (cli / "package.json").relative_to(root), checks)
        if manifest is None:
            continue
        try:
            package = json.loads(manifest)
            deps = package.get("dependencies", {})
            if not isinstance(deps, dict) or not all(
                isinstance(name, str) and re.fullmatch(r"(?:@[\w.-]+/)?[\w.-]+", name)
                and isinstance(version, str) and bool(version.strip())
                for name, version in deps.items()
            ):
                raise ValueError("invalid dependencies")
        except (ValueError, AttributeError):
            check(checks, f"portal:{skill.parent.name}", "error", "Invalid package manifest.",
                  "Restore cli/package.json before installing dependencies.")
            continue
        if not (cli / "src/cli.ts").is_file():
            check(checks, f"portal:{skill.parent.name}", "error", "CLI entry point is missing.",
                  "Restore cli/src/cli.ts.")
            continue
        # Dev types are unnecessary for running a zero-runtime-dependency CLI.
        missing = [name for name in deps
                   if not (cli / "node_modules" / name / "package.json").is_file()]
        if missing:
            check(checks, f"portal:{skill.parent.name}", "warning",
                  f"{len(missing)} runtime dependencies are not installed.",
                  f"Run bun install in {cli.relative_to(root).as_posix()}, or use the WebSearch fallback.")
        else:
            check(checks, f"portal:{skill.parent.name}", "ok", "Local CLI prerequisites are present.")
    if not enabled:
        check(checks, "portals", "warning", "No enabled portal CLIs were found.",
              "Enable a relevant installed portal or use the canonical WebSearch fallback.")
    queries = read_local(root, ".claude/skills/job-scraper/search-queries.md", checks)
    if queries is not None and PLACEHOLDER.search(without_comments(queries)):
        check(checks, "search-queries", "warning", "Search query templates still contain placeholders.",
              "Finish /setup, or supply explicit search terms and location for this run.")


def application_checks(root: Path, checks: list[dict]) -> None:
    for filename, engine in (("05-cv-templates.md", "lualatex"),
                             ("06-cover-letter-templates.md", "xelatex")):
        text = read_local(root, PROFILE_DIR / filename, checks)
        if text is None:
            continue
        if "<!-- BEGIN ACTIVE-TEMPLATE" in text:
            check(checks, f"template:{filename}", "warning",
                  "A custom template is active; its toolchain was not executed.",
                  "Read its ACTIVE-TEMPLATE block and verify the declared compile command.")
            continue
        present = bool(shutil.which(engine))
        check(checks, engine, "ok" if present else "error",
              f"{engine} is available on PATH." if present else f"{engine} is missing from PATH.",
              "Install the stock template's LaTeX toolchain using SETUP.md." if not present else "")
    extractor = importlib.util.find_spec("pypdf") is not None or bool(shutil.which("pdftotext"))
    check(checks, "pdf-text", "ok" if extractor else "warning",
          "A PDF text extractor is available." if extractor else "No PDF text extractor is available.",
          "Optional: python -m pip install pypdf for ATS checks." if not extractor else "")


def diagnose(root: Path = ROOT, scope: str = "all") -> dict:
    if scope not in SCOPES:
        raise ValueError(f"Unknown scope: {scope}")
    checks: list[dict] = []
    supported = sys.version_info >= (3, 10)
    check(checks, "python", "ok" if supported else "error",
          "Python 3.10+ is available." if supported else "Python 3.10+ is required.")
    if not root.is_dir():
        check(checks, "workspace", "error", "The workspace directory does not exist.",
              "Pass --root with the path of your AI Job Search checkout.")
    else:
        for relative in ("AGENTS.md", "CLAUDE.md", ".claude/commands/setup.md"):
            if not (root / relative).is_file():
                check(checks, "workspace", "error", f"Missing framework file: {relative}.",
                      "Pass --root with the framework checkout, or restore the missing file.")
        if scope in ("profile", "search", "apply", "all"):
            profile_checks(root, checks)
        if scope in ("search", "all"):
            search_checks(root, checks)
        if scope in ("apply", "all"):
            application_checks(root, checks)
    counts = {status: sum(row["status"] == status for row in checks)
              for status in ("ok", "warning", "error")}
    return {"scope": scope, "ready": counts["error"] == 0, "summary": counts, "checks": checks}


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="Framework checkout (defaults to this tool's repo)")
    parser.add_argument("--scope", choices=SCOPES, default="all")
    parser.add_argument("--format", choices=("plain", "json"), default="plain")
    args = parser.parse_args(argv)
    report = diagnose(args.root.resolve(), args.scope)
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"AI Job Search doctor ({args.scope}) - local prerequisites only")
        for row in report["checks"]:
            print(f"[{row['status'].upper()}] {row['name']}: {row['message']}")
            if row.get("fix"):
                print(f"  Next: {row['fix']}")
        counts = report["summary"]
        print(f"{counts['error']} error(s), {counts['warning']} warning(s).")
    return 0 if report["ready"] else 1


if __name__ == "__main__":
    sys.exit(main())
