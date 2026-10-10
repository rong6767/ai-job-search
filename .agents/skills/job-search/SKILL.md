---
name: job-search
description: >-
  Run this repository's job-search workflows: profile setup, multi-portal search,
  ranking, applications, outcomes and interview preparation. Use for managing a
  candidate's job search here, including Chinese requests such as 求职、岗位筛选、简历、求职信、面试准备.
  Repository code maintenance is outside this skill.
---

# AI Job Search for Codex

Use this skill in an AI Job Search checkout. The canonical workflows and candidate facts live in `.claude/` and `CLAUDE.md`; this skill routes to them rather than implementing a second workflow.

Read [Codex runtime bindings](references/codex-runtime.md), then read the selected specification below in full. Follow references from that specification only as needed. Resolve repository paths from the checkout containing [AGENTS.md](../../../AGENTS.md), even when Codex starts in a subdirectory.

## Select the workflow

For `$job-search <action> <arguments>`, use the action below. Interpret the text after the action as the canonical workflow's `$ARGUMENTS`: preserve flags, URLs and pasted posting text, including line breaks. A leading slash on an action (`/apply`) is an alias inside this skill, not a Codex slash-command registration.

- `setup`: [profile onboarding](../../../.claude/commands/setup.md)
- `scrape`: [multi-portal search](../../../.claude/skills/job-scraper/SKILL.md)
- `rank`: [shortlist ranking](../../../.claude/commands/rank.md)
- `apply`: [full application](../../../.claude/commands/apply.md)
- `interview`: [interview preparation](../../../.claude/commands/interview.md)
- `outcome`: [application outcome tracking](../../../.claude/commands/outcome.md)
- `upskill`: [learning from recorded skill gaps](../../../.claude/skills/upskill/SKILL.md)
- `expand`: [enrich a profile from verified sources](../../../.claude/commands/expand.md)
- `html-report`: [offline job-search report](../../../.claude/commands/html-report.md)
- `add-portal`: [register a portal CLI](../../../.claude/commands/add-portal.md)
- `add-template`: [register a document template](../../../.claude/commands/add-template.md)
- `reset`: [reset selected workspace data](../../../.claude/commands/reset.md)
- `gmail-sync`: [read application email updates](../../../.claude/commands/gmail-sync.md), when Gmail tools are connected
- `notion-sync`: [publish a Notion view](../../../.claude/commands/notion-sync.md), when Notion tools are connected

For a clear natural-language request, select the same workflow without requiring a command. For a CV-only, cover-letter-only or fit-only request, use the [application assistant's individual request rules](../../../.claude/skills/job-application-assistant/SKILL.md). An explicit single-portal lookup uses that portal's installed skill; a profile-based search across portals uses `scrape`.

An invocation without an action is not permission to start onboarding, search every portal, reset data or sync an account. Briefly explain the available actions and ask which task the user wants. An unknown action likewise needs clarification before executing anything. Reuse preferences and authorizations already supplied in the conversation.

The selected canonical workflow owns readiness checks, fit gates, drafting, validation and persistence. Selecting a skill adds no permission to submit applications, send email, publish data, install tools or bypass the host's sandbox.
