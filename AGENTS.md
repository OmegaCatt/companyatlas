# CompanyAtlas project notes

Read the parent portfolio plan and docs/PROJECT.md and docs/QA.md. Use fictional data only; never commit env files or secrets.

Backend authorization must precede retrieval, counts, file content and AI. Fixed-role local demo users use public demo passwords, not corporate SSO. Never describe them as protecting real data. Recheck identity after AI and source versions/hashes before returning citations. Deactivation invalidates all sessions of that identity. Client clearing must include previews and late requests.

Exact order calculations remain parameterized SQL. Imported PDF/DOCX text runs in a bounded subprocess; no OCR or original binary archive. Preserve source locators, version guards and atomic catalog revision updates. Do not allow document imports to overwrite prepared orders CSV.

Run requirements-dev.txt installation, unittest, offline evaluate.py, pnpm check and browser QA for related changes. Update Czech-first README and actual QA evidence. Live AI and mock browser answers must be labelled separately.
