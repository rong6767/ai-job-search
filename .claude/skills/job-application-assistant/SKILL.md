---
name: job-application-assistant
description: >
  Assists with job applications: evaluating job postings, tailoring CVs, writing cover letters,
  and preparing for interviews. Triggers on keywords like: job posting, job application, CV,
  cover letter, resume, interview prep, job fit, career, application, apply, ansøgning, stilling
allowed-tools: Read, Glob, Grep, WebFetch, WebSearch, Bash, Edit, Write, Agent, AskUserQuestion
framework_version: 1.3.5
---

# Job Application Assistant

---

## Workflow

For a full job application, read and execute **`.claude/commands/apply.md` from Step 0**, passing the user's posting URL or full pasted text as its input. This is the canonical application workflow, including readiness checks, fit evaluation and approval, active templates, the reviewer, compiled PDF inspection, ATS checks, and `/apply` Step 6b's tracker/posting archive. Follow it rather than running a separate drafting pipeline here.

The same rule applies when the user selects a result from `/scrape`. Keep the full posting text verbatim for the canonical archive; a quick scrape rating does not replace `/apply`'s evaluation. Reuse an approval already given for this application rather than asking for it again.

## Individual Requests

When the user explicitly asks for only one artifact or one step, use the corresponding references below. Do not create an application tracker row for a CV or cover letter drafted alone. If the request becomes a full application, return to the canonical `/apply` workflow.

### Step 1: Research & Evaluate Fit
- Run the read-only profile diagnostic (`python tools/doctor.py --scope profile`, using the available Python executable) before fetching or scoring. Resolve errors through `/setup`; warnings alone do not block evaluation.
- Fetch and research per `09-web-research.md`, retaining the **full posting text verbatim** if the user later proceeds.
- Evaluate with `04-job-evaluation.md`, including its eligibility and language gates, and present the assessment. Stop after evaluation unless the user requests drafting.

### Step 2: Tailor CV
- Follow `05-cv-templates.md` and `/apply` Step 2's CV guidance for factual grounding, filename derivation, and active-template handling; the **Subfolder naming** rule in `documents/README.md` applies before writing.
- Run the profile diagnostic from Step 1 above and check the CV template's compiler before writing. Follow `/apply` Step 5's compile, visual inspection and ATS checks for the CV before presenting it. Use the active template's extension and declared command.

### Step 3: Write Cover Letter
- Follow `03-writing-style.md`, `06-cover-letter-templates.md`, and `/apply` Step 2's cover-letter guidance for factual grounding, filename derivation and active-template handling.
- Run the profile diagnostic from Step 1 above and check the cover-letter template's compiler before writing. Follow `/apply` Step 5's compile and visual inspection for the cover letter before presenting it. Use the active template's extension and declared command.

### Step 4: Interview Preparation
- For a tracked application, read and execute `.claude/commands/interview.md` so preparation uses the submitted materials and interview history.
- For general interview practice, follow `07-interview-prep.md` using verified profile facts.

---

## Reference Files

| File | Purpose |
|------|---------|
| `01-candidate-profile.md` | Education, experience, skills, publications, awards |
| `02-behavioral-profile.md` | Behavioral assessment, strengths, ideal environments |
| `03-writing-style.md` | Tone, structure, do's and don'ts |
| `04-job-evaluation.md` | Scoring framework for job fit |
| `05-cv-templates.md` | LaTeX CV structure and tailoring rules |
| `06-cover-letter-templates.md` | LaTeX cover letter structure and tailoring rules |
| `07-interview-prep.md` | STAR examples, tough questions, roleplay guidelines |
| `08-application-forms.md` | Portal free-text fields: self-introduction, project entries, character-limited pitches |
| `09-web-research.md` | Fetching postings and company pages: trust boundary, the WebFetch 403 fallback, escalation order, claim verification |

---

## Quick Commands

The user may also ask for individual steps without the full workflow:
- "Evaluate this job posting" - Step 1 only
- "Write a CV for [company]" - Step 2 only
- "Write a cover letter for [role] at [company]" - Step 3 only
- "Help me prepare for an interview at [company]" - Step 4 only
- "What jobs should I look for?" - Career strategy discussion using profile + evaluation framework
