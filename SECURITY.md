# Security Policy

## Supported Versions

SHIELD is under active early-stage development on `master`. There are no
tagged releases yet, so only the latest commit on `master` is supported.

## Reporting a Vulnerability

If you discover a security vulnerability, please **do not** open a public
GitHub issue.

Instead, report it privately by:

- Using [GitHub's private vulnerability reporting](../../security/advisories/new)
  for this repository, or
- Emailing arvindnotie17@gmail.com with details and reproduction steps.

Please include:

- A description of the vulnerability and its potential impact
- Steps to reproduce, or a proof of concept
- Any relevant logs or affected files

You should expect an initial response within a few days. Once a fix is
available, we'll coordinate on disclosure timing before any public write-up.

## Scope

Given SHIELD handles user-submitted text/email content and JWT-based auth,
reports involving the following are especially relevant:

- Authentication/authorization bypass (`backend/app/core/security.py`, `backend/app/api/deps.py`)
- Injection via analyzed email/text content
- Secrets or API key exposure (e.g. `ANTHROPIC_API_KEY`, `JWT_SECRET`)
- Rate limiting / abuse of the AI analysis endpoints
