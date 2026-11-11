# Záznam skutečného průchodu

[Veřejný záznam v portfoliu](https://omegacatt.github.io/datadesk/portfolio/#companyatlas) ukazuje místní Python/SQLite server nad novou dočasnou fiktivní databází. Není to veřejně běžící backend. AI je při nahrávání výslovně vypnutá, nevznikají placená API volání.

Průchod: přihlášení provozního účtu → 12 objednávek roku 2024 → konkrétní řádky CSV → 5 objednávek pro Studio Javor (včetně jedné stornované) → přihlášení personálního účtu → odmítnutí dotazu na objednávky. Skript kontroluje výsledky, vymazání staré odpovědi a nepřítomnost JavaScript chyb. Nejde o měření obecné kvality AI nebo o důkaz produkčního zabezpečení.

## Opakování

Po instalaci requirements-dev.txt a pnpm install --frozen-lockfile:

```powershell
pnpm exec playwright install chromium ffmpeg
node scripts/record-demo.mjs
```

Výstup v docs/recording: WebM, poster PNG, české WebVTT titulky a JSON s časem pořízení, commitem aplikace, SHA-256 nahrávacího skriptu a kontrolovanými hodnotami. Volitelný první argument mění cílový adresář. ATLAS_PYTHON a PLAYWRIGHT_EXECUTABLE_PATH umožňují výslovně zvolit místní Python/prohlížeč. Skript nepoužívá existující uživatelskou databázi a po běhu svůj dočasný adresář odstraní.

První záznam vznikl z b0a9ba1. Rozšířený záznam ukazuje také personální podklad a osm kontrol vedení; přesný commit, čas a kontrolované hodnoty jsou v doprovodném companyatlas-recording.json veřejné galerie. Přiložené titulky popisují kroky; video nemá mluvený komentář. Veřejná demo hesla nejsou ochranou skutečných firemních dat. Další funkce včetně importu PDF/DOCX a AI mají samostatné testy/evaluaci uvedené v README a EVALUATION.md.

English: the public recording captures a real isolated local HTTP/SQLite walkthrough with fictional data, SQL counts, source rows and account-based denial. AI is disabled. Reproduce with the script above; the generated video, captions and provenance metadata are a recorded demonstration, not a hosted backend or a general AI accuracy claim.
