# Job Hunt Terminal

A small local job-search tool for one person. It finds broad European/remote jobs from Arbeitnow and Remotive, plus configured public Greenhouse, Lever and Ashby company boards; scores them against your local profile; records CVs and job decisions; and stores personalised emails as pending drafts.

It does not scrape LinkedIn, guess email addresses, bypass site controls, send bulk mail, or use a paid LLM API. Jobs are deduplicated by the source record and by normalized company, title and location across sources. A draft is sent only after its exact contents and PDF CV are printed and you type `SEND` in the terminal.

## Setup

From this folder, use a virtual environment and install the optional Gmail dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
jobhunt init
```

`jobhunt init` copies `profile.example.json` to `profile.json` and `sources.example.json` to `sources.json` if they do not exist. Both are deliberately gitignored. The source set starts with broad public feeds (Arbeitnow and Remotive) and also includes verified public company boards; change it freely as your target list evolves. Replace the example profile with your verified facts before relying on the scores.

For example, a Greenhouse job board at `boards.greenhouse.io/acme` normally uses `acme` as its `board`. The tool only calls the corresponding public board API. Do not add private URLs, credentials or sources whose access rules prohibit this use. `pages` on Arbeitnow is capped at 5 to respect the public feed.

## Daily flow

```powershell
jobhunt find
jobhunt jobs --min-score 70
jobhunt show 12
jobhunt set-status 12 interesting
jobhunt add-cv "Backend cloud CV" "C:\CVs\backend-cloud.pdf"
jobhunt prepare 12 --cv 1
jobhunt discover-contact 12
```

`prepare` prints a **writer packet**: the real job description, your availability, the selected CV path and only the facts you recorded in `profile.json`. In this Codex chat, ask me to prepare an email for that job; I can read the packet and write the text without any API key. Save the approved text in a UTF-8 file, then register it:

```powershell
jobhunt save-draft 12 --cv 1 --to "careers@company.com" --contact-source "https://company.com/careers" --subject "Backend Engineer — Your Name" --body-file .\email.txt
jobhunt drafts
```

The contact address must be publicly listed by the company. `discover-contact` looks only in the public job posting and job page, records any explicitly published address with its source URL, and reports none found rather than guessing. `save-draft` accepts either `--contact-id`, a manually supplied public `--to` and `--contact-source`, or no contact at all. A no-contact draft is saved as `needs_contact` and can never send; use `attach-contact DRAFT_ID --contact-id CONTACT_ID` to promote it to a pending draft. The tool preserves the evidence for review and refuses a second outreach draft to the same company for 30 days.

## Gmail (optional)

The tool uses Google OAuth, never a Gmail password. Create a **Desktop app** OAuth client in your own Google Cloud project, download its JSON as `credentials.json` in this folder, then run:

```powershell
jobhunt gmail-auth
jobhunt send 1
```

On first use, the browser opens for Google consent and `token.json` stays local. Use `jobhunt create-gmail-draft DRAFT_ID` to create a Gmail draft with the selected CV attached; it never sends. Before `jobhunt send DRAFT_ID` sends an email, the command prints the exact recipient, subject, full message and PDF path. Typing anything other than `SEND` cancels it. A successfully sent draft is marked `sent`, stores the Gmail message ID, and cannot be resent.

## Commands

| Command | Purpose |
| --- | --- |
| `jobhunt init` | Create local configuration and database. |
| `jobhunt find` | Fetch and score jobs from configured public sources. |
| `jobhunt jobs` | List ranked jobs; supports `--min-score`, `--status`, and `--limit`. |
| `jobhunt show ID` | Show a job, its description, and exact score reasons. |
| `jobhunt set-status ID STATUS` | Set `new`, `interesting`, `ignored`, `applied`, or `contacted`. |
| `jobhunt add-cv LABEL PDF` | Register a local PDF CV without copying it. |
| `jobhunt prepare ID --cv CV_ID` | Print the strict fact-only writer packet. |
| `jobhunt discover-contact ID` | Save only explicitly published emails from the job page. |
| `jobhunt contacts` | List saved public contact emails and their sources. |
| `jobhunt save-draft ...` | Save a pending email draft. |
| `jobhunt attach-contact DRAFT_ID --contact-id ID` | Attach a verified public contact to a saved no-contact draft. |
| `jobhunt create-gmail-draft DRAFT_ID` | Create a Gmail draft; never sends it. |
| `jobhunt gmail-auth` | Complete the one-time local Google OAuth consent flow. |
| `jobhunt send DRAFT_ID` | Display, confirm, then send one email via Gmail OAuth. |

## Checks

```powershell
python -m pytest -q
```

Tests cover deterministic scoring, senior-role penalties and source-level duplicate prevention.
