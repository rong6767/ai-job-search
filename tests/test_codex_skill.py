"""Keep the native Codex router connected to the canonical workflows.

Broken relative references or a newly added command with no route would leave
Codex using an incomplete second interface while Claude's commands still work.
The command inventory is derived from the canonical directory, not copied here.
"""

import re
import unittest
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = ROOT / ".agents/skills/job-search"
SKILL = SKILL_DIR / "SKILL.md"


class CodexWorkflowRoutingTests(unittest.TestCase):
    def test_every_canonical_command_has_its_own_route(self):
        text = SKILL.read_text(encoding="utf-8")
        entries = re.findall(r"^- `([^`]+)`: \[[^\]]+\]\(([^)]+)\)", text, re.MULTILINE)
        routes = dict(entries)
        self.assertEqual(len(entries), len(routes), "duplicate workflow actions")
        commands = sorted((ROOT / ".claude/commands").glob("*.md"))
        self.assertTrue(commands, "no canonical commands checked")
        for command in commands:
            with self.subTest(action=command.stem):
                self.assertIn(command.stem, routes, "canonical command is missing from Codex")
                self.assertEqual((SKILL_DIR / routes[command.stem]).resolve(), command.resolve())

    def test_all_local_references_resolve_inside_the_checkout(self):
        checked = 0
        for source in sorted(SKILL_DIR.rglob("*.md")):
            for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", source.read_text(encoding="utf-8")):
                parsed = urlsplit(target)
                if parsed.scheme or not parsed.path:
                    continue
                checked += 1
                resolved = (source.parent / parsed.path).resolve()
                with self.subTest(source=source.relative_to(ROOT), target=target):
                    self.assertTrue(resolved.is_relative_to(ROOT), "reference escapes the checkout")
                    self.assertTrue(resolved.is_file(), "referenced canonical file is missing")
        self.assertGreater(checked, 0, "no workflow references checked")


if __name__ == "__main__":
    unittest.main()
