"""Exercise the CLI subprocess preload without querying an external service."""

import shutil
import subprocess
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
BUN = shutil.which("bun")


@unittest.skipUnless(BUN, "Bun is required for the CLI preload smoke test")
class CliOfflineTests(unittest.TestCase):
    def test_preload_blocks_fetch_before_the_entry_point_can_read_a_response(self):
        # A data: URL makes the regression safe even if the guard is removed:
        # the unguarded branch only reads an in-memory fixture, never a portal.
        probe = """
try {
    const response = await fetch("data:text/plain,fixture");
    console.log(await response.text());
} catch (error) {
    console.log(error.message);
}
"""
        manifests = sorted((REPO_ROOT / ".agents" / "skills").glob("*/cli/package.json"))
        self.assertTrue(manifests, "No portal CLI manifests found")
        for manifest in manifests:
            with self.subTest(portal=manifest.parent.parent.name):
                tests = manifest.parent / "tests"
                preload = tests / "offline-preload.ts"
                self.assertTrue(preload.is_file(), "Portal tests need a local offline guard")
                helper = (tests / "helpers.ts").read_text(encoding="utf-8")
                self.assertIn('join(import.meta.dir, "offline-preload.ts")', helper)
                self.assertIn(
                    '["bun", "--no-install", "--preload", OFFLINE_PRELOAD, CLI_PATH, ...args]',
                    helper,
                )
                result = subprocess.run(
                    [BUN, "--no-install", "--preload", str(preload), "--eval", probe],
                    cwd=REPO_ROOT,
                    capture_output=True,
                    text=True,
                    timeout=15,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("OFFLINE_TEST_NETWORK_BLOCKED", result.stdout)
                self.assertNotIn("fixture", result.stdout)


if __name__ == "__main__":
    unittest.main()
