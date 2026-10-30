# CompanyAtlas project notes

Read `docs/PROJECT.md` and `docs/QA.md` before changing the app. Keep the sample company fictional and never commit `.env.local`, real credentials, personal records, or company files.

Preserve backend authorization before document retrieval, file content, counts, AI calls, and source citations. The passwordless role selector is only a demo and must never be described as production authentication. Keep exact order calculations in SQL and keep AI summaries limited to already-authorized source excerpts. Test cross-role leakage, stale browser state, and citation validation when modifying these flows.

Update README and QA evidence when behavior or scope changes. Do not claim PDF/DOCX import, arbitrary SQL, real-company deployment, or general multi-turn chat until implemented and verified.
