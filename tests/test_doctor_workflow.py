"""Regression guards for readiness and canonical application routing.

The markdown workflows are executable agent instructions. These checks catch
ordering and routing errors that would bypass an implemented diagnostic or the
review/compile pipeline, rather than duplicating the doctor's field logic.
"""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMMANDS = ROOT / ".claude" / "commands"
SCRAPER = ROOT / ".claude" / "skills" / "job-scraper" / "SKILL.md"
APPLICATION = ROOT / ".claude" / "skills" / "job-application-assistant" / "SKILL.md"


def section(text, heading):
    """Read one real section, avoiding unrelated mentions later in the file."""
    tail = text.split(heading, 1)[1]
    end = re.search(r"^#{1,4} ", tail, re.MULTILINE)
    return tail[:end.start()] if end else tail


class ReadinessRoutingTests(unittest.TestCase):
    def test_apply_checks_before_any_posting_fetch(self):
        text = (COMMANDS / "apply.md").read_text(encoding="utf-8")
        step = section(text, "## Step 0: Parse Input")
        self.assertLess(step.index("doctor.py --scope apply"), step.index("WebFetch"))
        self.assertIn("code 1, stop", step)
        self.assertIn("Warnings alone do not stop", step)
        self.assertIn("/setup", step)

    def test_scrape_checks_before_state_creation_and_health_needs_no_profile(self):
        text = SCRAPER.read_text(encoding="utf-8")
        step = section(text, "### Step 0: Load State")
        self.assertLess(step.index("doctor.py --scope search"), step.index("create if missing"))
        self.assertIn("code 1, stop", step)
        self.assertIn("For `/scrape health`, use `--scope setup`", step)
        self.assertIn("Skip the state creation", step)

    def test_rank_preserves_the_empty_batch_sweep_before_profile_gate(self):
        text = (COMMANDS / "rank.md").read_text(encoding="utf-8")
        step = section(text, "## Step 1: Load State")
        self.assertLess(step.index("rank_state.py sweep --write"), step.index("doctor.py --scope profile"))
        self.assertIn("code 1, stop before fetching or scoring", step)
        self.assertNotIn("doctor.py --scope apply", text)

    def test_setup_reports_diagnostics_without_blocking_unfilled_profile(self):
        text = (COMMANDS / "setup.md").read_text(encoding="utf-8")
        step = section(text, "## Step 0: Welcome & Choose Path")
        self.assertIn("doctor.py --scope setup", step)
        self.assertIn("does not block onboarding", step)
        self.assertIn("unfilled profile fields are expected", step)


class ApplicationRouteTests(unittest.TestCase):
    def test_full_application_is_a_pointer_to_all_apply_steps(self):
        text = APPLICATION.read_text(encoding="utf-8")
        workflow = section(text, "## Workflow")
        self.assertIn(".claude/commands/apply.md` from Step 0", workflow)
        for requirement in ("reviewer", "compiled PDF inspection", "ATS checks", "active templates"):
            self.assertIn(requirement, workflow)
        self.assertNotIn("### Step 3b", text)
        self.assertNotIn("main_<company>_<role>.tex", text)

    def test_selecting_a_scrape_result_runs_the_canonical_apply(self):
        text = SCRAPER.read_text(encoding="utf-8")
        route = text.split("If the user picks a number", 1)[1].split("\n\n", 1)[0]
        self.assertIn(".claude/commands/apply.md` from Step 0", route)
        self.assertIn("reviewer", route)
        self.assertIn("tracker recording", route)
        record = section(text, "### Step 6: Update Tracker (Optional)")
        self.assertIn("`/apply` Step 6b", record)
        self.assertIn("do not add a second row", record)

    def test_individual_artifacts_keep_verification_and_do_not_create_tracker_rows(self):
        text = APPLICATION.read_text(encoding="utf-8")
        individual = section(text, "## Individual Requests")
        self.assertIn("Do not create an application tracker row", individual)
        for heading in ("### Step 2: Tailor CV", "### Step 3: Write Cover Letter"):
            self.assertIn("Step 5", section(text, heading))


class ScrapeLanguageGateTests(unittest.TestCase):
    def test_undeclared_required_language_is_excluded_without_fit_scoring(self):
        text = SCRAPER.read_text(encoding="utf-8")
        assessment = section(text, "### Step 3: Quick Fit Assessment")
        for behavior in ("do not score", 'status: "skipped"', "fit: null", 'language_gate: "FAIL"', "**Excluded**"):
            self.assertIn(behavior, assessment)
        self.assertNotIn("mark it **Low**", assessment)
        self.assertIn("**FLAG**: assess fit normally", assessment)
        excluded = section(text, "### Excluded")
        self.assertIn("posting URL", excluded)
        self.assertIn("outside the match counts", excluded)


if __name__ == "__main__":
    unittest.main()
