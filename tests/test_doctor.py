"""Readiness checks must be scoped, offline and safe for personal profiles."""

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from tools import doctor


PROFILE = """## Identity
- **Name:** Test Candidate
- **Location:** Test City

### Languages
| Language | Level |
|----------|-------|
| English | Professional |

## Technical Skills
- Python: data pipelines
"""
# CLAUDE.md nests profile sections under ## Candidate Profile, while the
# canonical 01 profile uses ## directly. Mirror both shipped structures.
MAIN = "## Candidate Profile\n" + PROFILE.replace("## Identity", "### Identity").replace(
    "## Technical Skills", "### Technical Skills").replace(
    "- **Location:** Test City", "- **Location:** Test City\n- **CV language:** English")


class DoctorTests(unittest.TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.write("AGENTS.md", "Framework pointers")
        self.write("CLAUDE.md", MAIN)
        self.write(".claude/commands/setup.md", "Canonical setup")
        self.write(doctor.PROFILE_DIR / "01-candidate-profile.md", PROFILE)
        for name in ("05-cv-templates.md", "06-cover-letter-templates.md"):
            self.write(doctor.PROFILE_DIR / name, "Stock guidance")
        self.write(".claude/skills/job-scraper/search-queries.md", "site:example.com Python Test City")
        self.portal("global-search", deps={})
        self.which = patch.object(doctor.shutil, "which", return_value="available")
        self.which.start()
        self.addCleanup(self.which.stop)
        self.pdf = patch.object(doctor.importlib.util, "find_spec", return_value=object())
        self.pdf.start()
        self.addCleanup(self.pdf.stop)

    def write(self, relative, text):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def portal(self, name, enabled=True, deps=None):
        prefix = f".agents/skills/{name}"
        self.write(f"{prefix}/SKILL.md", f"---\nname: {name}\nenabled: {str(enabled).lower()}\n---\n")
        self.write(f"{prefix}/cli/package.json", json.dumps({"dependencies": deps or {}}))
        self.write(f"{prefix}/cli/src/cli.ts", "// entry")
        return prefix

    def errors(self, report):
        return [c["name"] for c in report["checks"] if c["status"] == "error"]

    def test_ready_checkout(self):
        report = doctor.diagnose(self.root)
        self.assertTrue(report["ready"], report)
        self.assertEqual(report["summary"]["error"], 0)

    def test_setup_needs_neither_initialized_profile_nor_bun_or_latex(self):
        self.write("CLAUDE.md", "[YOUR_NAME]")
        with patch.object(doctor.shutil, "which", return_value=None):
            report = doctor.diagnose(self.root, "setup")
        self.assertTrue(report["ready"], report)

    def test_template_profile_blocks_search_before_any_network_work(self):
        self.write("CLAUDE.md", MAIN.replace("Test Candidate", "[YOUR_NAME]"))
        report = doctor.diagnose(self.root, "search")
        self.assertFalse(report["ready"])
        self.assertIn("profile:CLAUDE.md", self.errors(report))

    def test_both_profile_sources_are_checked(self):
        self.write(doctor.PROFILE_DIR / "01-candidate-profile.md", PROFILE.replace("Professional", "[LEVEL]"))
        report = doctor.diagnose(self.root, "profile")
        self.assertFalse(report["ready"])
        self.assertIn("profile:.claude/skills/job-application-assistant/01-candidate-profile.md", self.errors(report))

    def test_empty_identity_values_do_not_borrow_the_next_field(self):
        for field, value in (("Name", "Test Candidate"), ("Location", "Test City"),
                             ("CV language", "English")):
            with self.subTest(field=field):
                self.write("CLAUDE.md", MAIN.replace(f"**{field}:** {value}", f"**{field}:** "))
                report = doctor.diagnose(self.root, "profile")
                self.assertIn("profile:CLAUDE.md", self.errors(report))

    def test_empty_skills_and_comment_only_language_do_not_count(self):
        text = PROFILE.replace("- Python: data pipelines", "- [OTHER_SKILLS]")
        text = text.replace("| English | Professional |", "<!-- | English | Professional | -->")
        self.write(doctor.PROFILE_DIR / "01-candidate-profile.md", text)
        report = doctor.diagnose(self.root, "profile")
        row = next(c for c in report["checks"] if c["status"] == "error")
        self.assertIn("skills", row["message"])
        self.assertIn("working languages", row["message"])

    def test_search_does_not_require_document_engines_or_dev_dependencies(self):
        with patch.object(doctor.shutil, "which", side_effect=lambda name: "bun" if name == "bun" else None):
            report = doctor.diagnose(self.root, "search")
        self.assertTrue(report["ready"], report)

    def test_profile_scope_does_not_require_search_tools(self):
        with patch.object(doctor.shutil, "which", return_value=None):
            report = doctor.diagnose(self.root, "profile")
        self.assertTrue(report["ready"], report)

    def test_missing_bun_allows_websearch_fallback(self):
        with patch.object(doctor.shutil, "which", return_value=None):
            report = doctor.diagnose(self.root, "search")
        self.assertTrue(report["ready"], report)
        self.assertEqual(next(c for c in report["checks"] if c["name"] == "bun")["status"], "warning")

    def test_disabled_portal_dependencies_are_ignored(self):
        self.portal("local-search", enabled=False, deps={"parser": "1.0"})
        report = doctor.diagnose(self.root, "search")
        self.assertTrue(report["ready"], report)
        self.assertNotIn("portal:local-search", [c["name"] for c in report["checks"]])

    def test_workflow_skills_are_not_portal_candidates(self):
        self.write(".agents/skills/job-search/SKILL.md", "---\nname: job-search\n"
                   "description: Run canonical workflows\n---\n")
        report = doctor.diagnose(self.root, "search")
        self.assertTrue(report["ready"], report)
        self.assertFalse(any("job-search" in c["name"] for c in report["checks"]))

    def test_workflow_skill_does_not_count_as_an_enabled_portal(self):
        self.write(".agents/skills/job-search/SKILL.md", "---\nname: job-search\n---\n")
        self.portal("global-search", enabled=False)
        report = doctor.diagnose(self.root, "search")
        self.assertEqual(next(c for c in report["checks"] if c["name"] == "portals")["status"], "warning")

    def test_incomplete_portal_cli_is_reported(self):
        (self.root / ".agents/skills/global-search/cli/package.json").unlink()
        report = doctor.diagnose(self.root, "search")
        self.assertIn(".agents/skills/global-search/cli/package.json", self.errors(report))

    def test_future_portals_do_not_require_a_search_name_suffix(self):
        self.portal("new-board")
        report = doctor.diagnose(self.root, "search")
        self.assertEqual(next(c for c in report["checks"] if c["name"] == "portal:new-board")["status"], "ok")

    def test_enabled_portal_reports_missing_scoped_runtime_dependency(self):
        prefix = self.portal("local-search", deps={"@scope/parser": "1.0"})
        report = doctor.diagnose(self.root, "search")
        self.assertEqual(next(c for c in report["checks"] if c["name"] == "portal:local-search")["status"], "warning")
        self.write(f"{prefix}/cli/node_modules/@scope/parser/package.json", "{}")
        report = doctor.diagnose(self.root, "search")
        self.assertEqual(next(c for c in report["checks"] if c["name"] == "portal:local-search")["status"], "ok")

    def test_skills_section_does_not_consume_neighboring_profile_sections(self):
        self.write("CLAUDE.md", MAIN.replace("- Python: data pipelines", "") +
                   "\n### Certifications\n- Completed training\n")
        self.assertIn("profile:CLAUDE.md", self.errors(doctor.diagnose(self.root, "profile")))

    def test_invalid_manifest_reports_error_instead_of_crashing(self):
        self.write(".agents/skills/global-search/cli/package.json", "[]")
        self.assertIn("portal:global-search", self.errors(doctor.diagnose(self.root, "search")))

    def test_dependency_paths_cannot_escape_node_modules(self):
        self.portal("bad-search", deps={"../../private": "1.0"})
        self.assertIn("portal:bad-search", self.errors(doctor.diagnose(self.root, "search")))

    def test_invalid_enabled_flag_is_reported(self):
        self.write(".agents/skills/global-search/SKILL.md", "---\nenabled: sometimes\n---\n")
        self.assertIn("portal:global-search", self.errors(doctor.diagnose(self.root, "search")))

    def test_queries_with_placeholders_only_warn_for_explicit_searches(self):
        self.write(".claude/skills/job-scraper/search-queries.md", "[YOUR_PRIMARY_ROLE_TYPE]")
        report = doctor.diagnose(self.root, "search")
        self.assertTrue(report["ready"], report)
        self.assertEqual(next(c for c in report["checks"] if c["name"] == "search-queries")["status"], "warning")

    def test_stock_apply_requires_both_engines(self):
        with patch.object(doctor.shutil, "which", return_value=None):
            report = doctor.diagnose(self.root, "apply")
        self.assertIn("lualatex", self.errors(report))
        self.assertIn("xelatex", self.errors(report))
        self.assertNotIn("bun", self.errors(report))

    def test_custom_templates_do_not_require_stock_engines(self):
        for name in ("05-cv-templates.md", "06-cover-letter-templates.md"):
            self.write(doctor.PROFILE_DIR / name, "<!-- BEGIN ACTIVE-TEMPLATE -->\nCompile with typst\n<!-- END ACTIVE-TEMPLATE -->")
        with patch.object(doctor.shutil, "which", return_value=None):
            report = doctor.diagnose(self.root, "apply")
        self.assertTrue(report["ready"], report)
        self.assertEqual(report["summary"]["warning"], 2)

    def test_pdf_extractor_is_optional(self):
        with patch.object(doctor.importlib.util, "find_spec", return_value=None), \
                patch.object(doctor.shutil, "which", side_effect=lambda name: None if name == "pdftotext" else "available"):
            report = doctor.diagnose(self.root, "apply")
        self.assertTrue(report["ready"], report)
        self.assertEqual(next(c for c in report["checks"] if c["name"] == "pdf-text")["status"], "warning")

    def test_missing_and_non_utf8_files_fail_cleanly(self):
        (self.root / "CLAUDE.md").unlink()
        (self.root / doctor.PROFILE_DIR / "01-candidate-profile.md").write_bytes(b"\xff\xff")
        self.assertFalse(doctor.diagnose(self.root, "profile")["ready"])

    def test_report_does_not_contain_personal_values(self):
        report = json.dumps(doctor.diagnose(self.root))
        self.assertNotIn("Test Candidate", report)
        self.assertNotIn("Test City", report)
        self.assertNotIn("data pipelines", report)

    def test_real_cli_from_different_directory_returns_json_and_exit_code(self):
        env = dict(os.environ, PYTHONIOENCODING="cp1252", PYTHONUTF8="0")
        tool = Path(doctor.__file__).resolve()
        proc = subprocess.run([sys.executable, str(tool), "--root", str(self.root),
                               "--scope", "setup", "--format", "json"],
                              cwd=self.root, env=env, capture_output=True)
        self.assertEqual(proc.returncode, 0, proc.stderr.decode("utf-8"))
        self.assertTrue(json.loads(proc.stdout.decode("utf-8"))["ready"])
        self.write("CLAUDE.md", "[YOUR_NAME]")
        proc = subprocess.run([sys.executable, str(tool), "--root", str(self.root),
                               "--scope", "profile", "--format", "json"], capture_output=True)
        self.assertEqual(proc.returncode, 1)
        self.assertFalse(json.loads(proc.stdout)["ready"])

    def test_real_cli_search_ignores_workflow_router_without_a_cli(self):
        self.write(".agents/skills/job-search/SKILL.md", "---\nname: job-search\n"
                   "description: Codex workflow router\n---\n")
        proc = subprocess.run([sys.executable, str(Path(doctor.__file__).resolve()),
                               "--root", str(self.root), "--scope", "search", "--format", "json"],
                              cwd=self.root, capture_output=True)
        self.assertEqual(proc.returncode, 0, proc.stderr.decode("utf-8"))
        report = json.loads(proc.stdout)
        self.assertTrue(report["ready"], report)
        self.assertFalse(any("job-search" in c["name"] for c in report["checks"]))


if __name__ == "__main__":
    unittest.main()
