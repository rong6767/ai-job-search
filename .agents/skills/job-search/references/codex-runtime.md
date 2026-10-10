# Codex runtime bindings

These bindings translate execution capabilities. The selected `.claude/` specification remains the source of workflow rules, output formats and candidate facts. Read `CLAUDE.md` and its required profile/methodology references when the workflow calls for them; a Claude-named file does not require the Claude runtime.

## Paths and local tools

Use the repository root as the working directory for `tools/`, portal CLIs, trackers, `job_scraper/`, `company_research/` and `upskill/`. A reference such as `search-queries.md` means the file beside its canonical skill, never beside this router. Do not create state inside `.agents/skills/job-search/` or nest output under `.claude/skills/`.

Map `Read`, `Glob` and `Grep` to local file reads and `rg`/`rg --files`; map `Write`/`Edit` to file tools or `apply_patch`. Map `Bash` to the available shell/command tool. Use the Python 3.10+ executable available on PATH (`python`, `python3` or `py`) and the existing Bun CLIs. Claude's `allowed-tools`, `context: fork` and `.claude/settings.json` are Claude metadata, not Codex permissions.

On Windows, translate shell operations to PowerShell, use `curl.exe` for curl, and use a Python temporary-directory helper or PowerShell here-string for multiline input. Pass arguments as data; do not expand job text, `$ARGUMENTS` or a pasted document as shell code. Preserve the canonical build's success checks and cleanup behavior when translating Bash commands. The `/reset` confirmation and scoped deletion rules still apply, using the host's native file operations.

## Research, questions and delegation

Map `WebSearch` to the session's web search and `WebFetch` to web opening, an available browser or an appropriate HTTP client, following the canonical research trust boundaries and retry order. If research is unavailable, report the limitation and use the workflow's pasted-posting path where supported. Do not fabricate listings, sources or company claims. The existing `robots_check.py` uses its declared crawler identity; passing it is not a claim about every Codex or OpenAI user agent.

Map `AskUserQuestion` to the host's user-input tool where available, or an ordinary question followed by waiting for the answer. Never treat elapsed time as consent. Honor prior authorization rather than asking again solely because the canonical instructions use another runtime's tool name.

Map `Agent` / `general-purpose` to Codex subagents when available. For `/apply`'s reviewer, use an independent context and supply the canonical reviewer prompt, drafts, necessary rubric/profile facts and these runtime bindings inline. Keep the required company verification with the orchestrator. Parallel portal queries and `/rank` batches can run sequentially when delegation is unavailable. If an independent reviewer cannot run, state that the reviewer step is incomplete; do not describe self-review as a completed second-agent review or silently mark the application final.

## Compile and inspect documents

Use the real compiler declared by the active template, from the correct output directory. Stock documents need the repository's LaTeX toolchain and bundled class/fonts. A standalone `.tex` preview compiler that cannot load additional project files is not a substitute for that build.

Run the canonical page-count, PDF text and layout checks with the existing helpers. For visual inspection, render every PDF page with an available PDF renderer (for example `pdftoppm -png` into a temporary directory), then inspect the rendered pages with the host's image viewer. Reading PDF bytes or extracting text alone does not verify visual layout. If rendering is unavailable, report visual verification as incomplete and explain the missing tool; never claim it passed. Retain the active template's page limits and the canonical compile/inspect loop.

## Optional account integrations

Discover Gmail or Notion by the tools actually exposed in the current session, including their descriptions; do not require Claude-specific tool-name prefixes. Use only a connected integration with equivalent capabilities, and keep the canonical read/write limits, approval checkpoints and sync schema. If tools or authentication are unavailable, report that the integration must be connected in the user's Codex host and stop that action. Do not run `claude mcp` or silently replace a connector with shell, IMAP or stored credentials. Do not start an OAuth flow during a sync command.

## Candidate facts and runtime identity

Adapt onboarding greetings and generated report metadata to the runtime actually used. Tool names in a candidate's CV or cover letter are factual claims: use the verified profile. Do not replace an established `Claude Code` skill with `Codex` merely because Codex is running the workflow, or invent proficiency in either product. If a canonical wording instruction conflicts with the verified candidate facts, surface the conflict before including the claim.
