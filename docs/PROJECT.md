# UX-1 až UX-7 – 11. 11. 2026

Každý účet má tři skutečné pracovní situace a sadu příkladů: provoz otevírá objednávky a dodavatele, personální tým zaškolení/dovolenou/osobní podklad, vedení interní plán a kontrolní panel. Tlačítka otevírají pouze soubory dostupné přihlášené roli; příprava otázky sama AI nevolá.

Všech sedm aplikací má první přístupný dialog a stálé ovládání nápovědy v hlavičce. Playwright ověřuje skutečný první vstup, obě části, GitHub odkaz, Tab/Shift+Tab, Escape, návrat fokusu, potvrzení po reloadu a mobil. CompanyAtlas čeká s přihlášením na zavření úvodu; hlavička se testuje po přihlášení. Legacy pracovní průchody pokračují po skutečném zavření úvodu. Aktuální commit, CI a přesný rozsah ověření této etapy jsou vedené v hlavním Portfolio_PROGRESS.md; starší zápisy níže jsou historické.

# Etapa ukázky 11. 11. 2026

Veřejné portfolio má skutečnou krátkou nahrávku místního SQL/zdroj/oprávnění průchodu s vypnutou AI. Reprodukce docs/DEMO.md. Aplikační backend této etapy zůstal na již ověřeném kódu b0a9ba1; přibyl vývojový nahrávací skript a jeho syntax check. Znovu prošlo 27 Python testů, 50 offline případů a browser sada.

# Aktuální rozsah a kontrola 10. 11. 2026

Aktuální funkce, technologie, API, způsob použití, firemní zavedení a omezení jsou v [README](../README.md). Znovu prošlo 27 Python testů a odpovídající skutečný browser průchod desktop/mobil. Jde o fiktivní portfolio projekt. Výsledky a případné opravy jsou v [QA](QA.md).

Předchozí ověřený kód 194d883: [úspěšné GitHub Actions](https://github.com/OmegaCatt/companyatlas/actions/runs/42729784052). Nový commit této revize má vlastní CI; aktuální stav je v hlavním protokolu portfolia. Níže uvedené historické plány nejsou seznam nehotových funkcí.

<details>
<summary>Historická projektová rozhodnutí a průběžné etapy</summary>

# Závěrečná kontrola CA-1d / CA-2b/c

27 Python testů a 50 offline případů prošlo. Složený zákazník před „v letech“, všechna rozmezí a další výslovné roky jsou zachované; od roku/do roku i odmítnutí nepodporované částky mají regresi. Dva širší živé běhy vyšly 17/17 a 17/17; zprávy jsou v evaluation-2026-11-10-full-1.json a full-2.json. Neshody ani chybné citace tyto dva běhy neukázaly. Viz EVALUATION.md pro ruční kontrolu a omezení.

# Aktuální etapa 10. 11. 2026 – CA-4/5

Pevné ukázkové účty, scrypt a odhlášení; deaktivace ruší relace i rozpracovanou odpověď. Vedení importuje textové PDF/DOCX/TXT/MD v omezeném procesu; lokátory, SHA-256, atomická verze/index a mazání. Staré odkazy vracejí konflikt, změna podkladu během AI ruší citace. Původní binární soubor ani úplný archiv verzí se neukládá. Veřejné demo heslo nechrání skutečná data. Aktuální limity a instalace jsou v README.

Ověření: 25 Python testů včetně skutečného PDF/DOCX, pozdější strany v AI úryvku, české diakritiky, skenu bez textu, XML entit, verzí, mazání, rolí a odebrání identity během odpovědi. 50 offline případů. Browser QA prošlo: reálné přihlášení, PDF import, výměna za DOCX, smazání, filtrování, živé odpojení účtu přes druhou relaci, SQL, citace s výslovně simulovanou odpovědí, klávesnice a mobil bez přetečení/JS chyb. Nové živé AI volání neproběhlo. Vizuálně zkontrolovaný snímek správy je management.png. CI této změny zatím čeká na publikaci.

## Historické záznamy (nepopisují aktuální rozsah)

# Druhá etapa 9. 11. 2026 – CA-1a/b/c, CA-2a a CA-3a

18 automatických testů prošlo. Samostatná offline evaluace 50/50 má 16 metrik, 10 upřesnění, 6 odmítnutí přístupu, 14 vyhledání textových zdrojů a 4 dotazy bez podkladu. Živý běh před úpravou vykázal 6/8; po explicitním `supported` a opravě příliš přísného očekávání u časové otázky nový běh 8/8. Odpovědi byly posouzeny vůči zdrojům; podrobnosti, oba reporty a hranice jsou v EVALUATION.md. Nejde o obecnou přesnost ani úplné ověření prompt injection.

Browser QA na skutečném serveru s vypnutým API: SQL dotaz, odmítnutí průměru, boční náhled, Escape a vrácení fokusu, jedna simulovaná AI odpověď pro zobrazení citátu, zadržená odpověď souboru po změně role, vymazání obsahu, odmítnutý přístup k objednávkám, desktop 1440 px a mobil 390 px bez přetečení/JS chyb. Mobilní náhled brání fokusu do zakryté plochy, Tab přepíná zavření a posouvatelný obsah.

CI nově spouští unittest, offline evaluaci a browser QA bez klíče; nahrává report a screenshoty. Vzdálený výsledek této etapy ještě nebyl ověřen. PDF/DOCX, životní cyklus indexu, pevná identita a širší opakovaná živá evaluace zůstávají otevřené.

Následující zápisy jsou historické etapy.

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


</details>
