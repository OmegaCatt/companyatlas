# Etapa 9. 11. 2026

15 automatických testů prošlo, nová kontrola obsahuje 16 datových podscénářů. Izolovaný browser QA server s vypnutým AI ověřil součet let 2024 a 2025, filtr stornovaných, upřesnění měsíčního dotazu, vymazání odpovědi po změně role, nepřístupnost seznamu objednávek pro personální roli a mobilní 390 px bez přetečení/JS chyb. Autentizace, PDF/DOCX a rozšířená sada textových AI evaluací zůstávají další etapou.

# CompanyAtlas — project memory

Updated 2026-10-30. Third portfolio application after DataDesk and OfferLens. The user requested a company-file explorer that answers natural-language questions, including exact order counts, while applying different access rights to departments.

## Goal

Demonstrate Python, SQL, document retrieval, AI integration, role-aware access, source evidence, and QA in one fictional business scenario. This should complement DataDesk's data validation and OfferLens's quote comparison.

## V1 decisions

- Use a fictional company, Severka Studio, with 9 curated CSV/Markdown files and 15 orders. No personal CV data or real customer records.
- Roles: operations/purchasing, people, leadership. Operations is a better fit for the sample order and supplier workflow than a narrow accounting role; the role model remains configurable in principle.
- Count orders and sum their value in parameterized SQLite queries. Include cancelled rows in the count and display their status separately. Ambiguous customer names require clarification.
- Filter file metadata, content, retrieval, and counts on the backend before invoking AI. Never rely on the model to enforce permissions.
- Use OpenAI Responses API only for text-document summaries. Require exact evidence quotes from already-authorized sources; do not claim that this proves the answer's meaning.
- Use passwordless demo-role switching only with fictional data. A real deployment needs authentication, source ACL synchronization, durable rate limits, and a security review.
- Keep the API key in ignored `.env.local` or a process variable. The repository contains only `.env.example`.
- Use Python standard library only so the project runs without package installation. The tested runtime is Python 3.13.17.

## Verified status

14 automated tests pass. Browser walkthrough covered order counts, role filtering, forbidden query, role-change stale-answer cleanup, live AI summary with a matching evidence quote, and leadership QA panel. A later browser regression also verified the expandable technical note and downloading an authorized answer with its sources and counted rows. README and QA.md contain current limits and results.
The visual layer was simplified on 2026-10-30: a neutral document-workspace palette, plain headings and controls, and no decorative AI orbit. Authorization and answer behavior were left intact; desktop and mobile browser checks were repeated.

## Next scope candidates

Authenticated demo users, incremental indexing, PDF/DOCX import, more supported analytic intents, persistent cross-run evaluations, and a deployment with durable usage limits. None are implemented in V1.
