# Security Policy

## Supported Versions

| Version | Supported |
|---|---|
| `v0.x.x-alpha` | ✅ Active development — patches applied promptly |

MindVault is currently in alpha. Security fixes are prioritised over new features.

---

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Please report security issues privately by emailing the maintainer or using GitHub's private vulnerability reporting feature (Security → Report a vulnerability).

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

You will receive a response within **72 hours** acknowledging the report. We aim to release a patch within **14 days** of a confirmed vulnerability.

---

## Scope

The following are **in scope**:

- SQL injection via unsanitised FTS queries
- Path traversal in document ingestion (file upload endpoint)
- Prompt injection attacks on the AI assistant
- API key exposure in logs, error messages, or API responses
- Insecure deserialization of user-supplied data

The following are **out of scope**:

- Vulnerabilities in third-party libraries that are already publicly known (report to upstream)
- Issues requiring physical access to the machine
- Denial-of-service via large file uploads (rate limiting is a planned feature)

---

## Security Design Principles

MindVault is designed with the following security properties:

1. **No network by default**: Core vault, search, graph, and reasoning work 100% offline.
2. **API keys via environment variables only**: Never stored in code, committed to git, or logged. See `.env.example`.
3. **File type validation**: Document ingestion only accepts `.pdf` and `.txt` with MIME-type checks.
4. **SHA-256 provenance**: Every ingested document and timeline event is content-fingerprinted.
5. **Input sanitization**: FTS5 queries are parameterised; file paths are canonicalized before access.
6. **No remote execution**: The AI assistant only reads from your local vault; it never executes arbitrary code.

---

## Dependency Audit

Run `pip audit` periodically to check for known CVEs in installed packages:

```powershell
.venv\Scripts\pip.exe install pip-audit
.venv\Scripts\pip-audit.exe
```
