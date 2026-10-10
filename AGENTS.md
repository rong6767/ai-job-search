---
framework_version: 1.1.0
---

# Agent Guidelines: AI Job Search

This workspace is structured to manage job search activities, scraper tools, CVs, cover letters, and interview preparation.

## Thin-Pointer Design (Single Source of Truth)

To prevent duplication and configuration drift across different AI agent frameworks (Claude Code, Google Antigravity, Codex, Cursor, Gemini CLI, etc.), this workspace uses a unified thin-pointer design. All agent runtimes should load the canonical specifications and candidate profiles from the files and directories below:

1. **Personal Candidate Profile:**
   - The candidate profile, contact details, education, and target preferences are defined in [CLAUDE.md](CLAUDE.md) and the individual profile methodology files under [.claude/skills/job-application-assistant/](.claude/skills/job-application-assistant/) (specifically `01-*.md` etc.).
2. **Canonical Workflow Specifications:**
   - The step-by-step instructions and triggers for tasks (setup, scrape, rank, apply, upskill, interview) are defined in the [.claude/](.claude/) directory (specifically under `.claude/skills/` and `.claude/commands/`).
   - Do not duplicate these rules or specifications. Treat `.claude/` files as the single source of truth.
3. **Portal Search Skills:**
   - Job-portal search CLIs live under [.agents/skills/](.agents/skills/) in the portable Agent Skills format (with a `SKILL.md` per portal). Codex and Antigravity discover these automatically; the `/scrape` workflow in [.claude/skills/job-scraper/](.claude/skills/job-scraper/) orchestrates them.

## Direct Codex Support

For job-search workflow requests, use the repository's [job-search skill](.agents/skills/job-search/SKILL.md). Users can invoke `$job-search setup`, `$job-search scrape`, `$job-search rank`, `$job-search apply <posting>`, or ask for the same tasks in natural language. These are skill actions; `.claude/commands/` files are not registered Codex slash commands.

Read the selected canonical specification through that skill and apply its [Codex runtime bindings](.agents/skills/job-search/references/codex-runtime.md). Preserve the user's arguments, existing authorization, workflow checks and candidate facts. Treat Claude-specific tool names as capabilities to map to the current session, not as commands to call literally. Repository development and maintenance requests do not invoke the job-search workflow.

Keep workflow rules and candidate profiles in `.claude/` and `CLAUDE.md`; the Codex skill provides routing and runtime bindings only. Do not copy profile data into `.agents/` or create a second set of workflow commands.
