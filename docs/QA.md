# Regrese UX-1b – rychlé zavření a reload

První Linux main CI odhalilo závod: potvrzení úvodu v události close se někdy nestihlo zapsat před reloadem. Nyní se zapisuje synchronně v Escape/cancel a tlačítkách před zavřením; close je záložní cesta. Původní neúspěšný běh zůstává v Actions. Browser test stále provádí okamžitý reload, očekávání nebylo oslabeno ani přidán čekací čas.

# UX-1 až UX-7 – 11. 11. 2026

Nová regrese vyžaduje konkrétní expected/actual a skutečnou existenci zdroje v kontrolách oprávnění. Browser prověřil tři situace každé role, osobní podklad, 403 kontrolního API pro provoz a vedením znovu provedených 8/8 kontrol. Offline sada 50/50 není živé měření AI.

Místně ověřené unit testy: **28 Python**.

Každý účet má tři skutečné pracovní situace a sadu příkladů: provoz otevírá objednávky a dodavatele, personální tým zaškolení/dovolenou/osobní podklad, vedení interní plán a kontrolní panel. Tlačítka otevírají pouze soubory dostupné přihlášené roli; příprava otázky sama AI nevolá.

Všech sedm aplikací má první přístupný dialog a stálé ovládání nápovědy v hlavičce. Playwright ověřuje skutečný první vstup, obě části, GitHub odkaz, Tab/Shift+Tab, Escape, návrat fokusu, potvrzení po reloadu a mobil. CompanyAtlas čeká s přihlášením na zavření úvodu; hlavička se testuje po přihlášení. Legacy pracovní průchody pokračují po skutečném zavření úvodu. Aktuální commit, CI a přesný rozsah ověření této etapy jsou vedené v hlavním Portfolio_PROGRESS.md; starší zápisy níže jsou historické.

# Nahrávka 11. 11. 2026 – DEMO-5

Skutečný izolovaný HTTP/SQLite průchod b0a9ba1: 12 objednávek, zdroj CSV, 5 pro Studio Javor, změna účtu a odmítnutí přístupu; žádné JS chyby. Výstup 27,48 s a osm českých titulků. AI vypnutá; nahrávka není novou evaluací AI. Reprodukce docs/DEMO.md a scripts/record-demo.mjs. Přidána kontrola syntaxe skriptu.

# Opakované ověření 10. 11. 2026

**27 Python testů prošlo.** Znovu spuštěné prohlížečové QA ověřilo skutečný pracovní postup na dočasných fiktivních podkladech, desktop i mobil a JavaScript chyby. Navíc jeden nový skutečný AI dotaz nad fiktivním textem prošel (1/1) a offline sada 50/50. Je to aktuální smoke test, nikoli nová reprezentativní míra přesnosti.

Ověřený předchozí commit 194d883: [GitHub Actions](https://github.com/OmegaCatt/companyatlas/actions/runs/42729784052); dostupnost jeho artefaktů byla ověřena. Aktuální revize dokumentace/oprav je kontrolována novým CI. Jeho přesný commit a výsledek jsou v hlavním Portfolio_PROGRESS.md. Staré věty o čekající publikaci v rozbaleném archivu platily jen pro dobu daného zápisu.

<details>
<summary>Historické výsledky, původní metriky a omezení</summary>

# Závěrečná kontrola CA-1d / CA-2b/c

27 Python testů a 50 offline případů prošlo. Složený zákazník před „v letech“, všechna rozmezí a další výslovné roky jsou zachované; od roku/do roku i odmítnutí nepodporované částky mají regresi. Dva širší živé běhy vyšly 17/17 a 17/17; zprávy jsou v evaluation-2026-11-10-full-1.json a full-2.json. Neshody ani chybné citace tyto dva běhy neukázaly. Viz EVALUATION.md pro ruční kontrolu a omezení.

# Aktuální etapa 10. 11. 2026 – CA-4/5

Pevné ukázkové účty, scrypt a odhlášení; deaktivace ruší relace i rozpracovanou odpověď. Vedení importuje textové PDF/DOCX/TXT/MD v omezeném procesu; lokátory, SHA-256, atomická verze/index a mazání. Staré odkazy vracejí konflikt, změna podkladu během AI ruší citace. Původní binární soubor ani úplný archiv verzí se neukládá. Veřejné demo heslo nechrání skutečná data. Aktuální limity a instalace jsou v README.

Ověření: 25 Python testů včetně skutečného PDF/DOCX, pozdější strany v AI úryvku, české diakritiky, skenu bez textu, XML entit, verzí, mazání, rolí a odebrání identity během odpovědi. 50 offline případů. Browser QA prošlo: reálné přihlášení, PDF import, výměna za DOCX, smazání, filtrování, živé odpojení účtu přes druhou relaci, SQL, citace s výslovně simulovanou odpovědí, klávesnice a mobil bez přetečení/JS chyb. Nové živé AI volání neproběhlo. Vizuálně zkontrolovaný snímek správy je management.png. CI této změny zatím čeká na publikaci.

## Historické záznamy (nepopisují aktuální rozsah)

## Ověřený vzdálený běh

GitHub Actions úspěšně ověřily kód `e267526`: [výsledek kontroly](https://github.com/OmegaCatt/companyatlas/actions/runs/42685515544). Výsledek se vztahuje k uvedenému commitu; změny pouze dokumentace nepřidávají nové funkce.

# Druhá etapa 9. 11. 2026 – CA-1a/b/c, CA-2a a CA-3a

18 automatických testů prošlo. Samostatná offline evaluace 50/50 má 16 metrik, 10 upřesnění, 6 odmítnutí přístupu, 14 vyhledání textových zdrojů a 4 dotazy bez podkladu. Živý běh před úpravou vykázal 6/8; po explicitním `supported` a opravě příliš přísného očekávání u časové otázky nový běh 8/8. Odpovědi byly posouzeny vůči zdrojům; podrobnosti, oba reporty a hranice jsou v EVALUATION.md. Nejde o obecnou přesnost ani úplné ověření prompt injection.

Browser QA na skutečném serveru s vypnutým API: SQL dotaz, odmítnutí průměru, boční náhled, Escape a vrácení fokusu, jedna simulovaná AI odpověď pro zobrazení citátu, zadržená odpověď souboru po změně role, vymazání obsahu, odmítnutý přístup k objednávkám, desktop 1440 px a mobil 390 px bez přetečení/JS chyb. Mobilní náhled brání fokusu do zakryté plochy, Tab přepíná zavření a posouvatelný obsah.

CI nově spouští unittest, offline evaluaci a browser QA bez klíče; nahrává report a screenshoty. Vzdálený výsledek kódu je úspěšně ověřen; viz odkaz v úvodu. PDF/DOCX, životní cyklus indexu, pevná identita a širší opakovaná živá evaluace zůstávají otevřené.

Následující zápisy jsou historické etapy.

# Ověření 9. 11. 2026

15 automatických testů prošlo, nová kontrola obsahuje 16 datových podscénářů. Izolovaný browser QA server s vypnutým AI ověřil součet let 2024 a 2025, filtr stornovaných, upřesnění měsíčního dotazu, vymazání odpovědi po změně role, nepřístupnost seznamu objednávek pro personální roli a mobilní 390 px bez přetečení/JS chyb. Autentizace, PDF/DOCX a rozšířená sada textových AI evaluací zůstávají další etapou.

# Ověření CompanyAtlas

## Doplnění 31. 10. 2026: vysvětlení a předání odpovědi

Automatické serverové testy prošly 14/14. Prohlížečový průchod otevřel nový technický přehled, položil přesný dotaz na rok 2024, stáhl odpověď se zdroji a započítanými řádky a ověřil, že změna role odpověď skryje. Mobilní viewport 390 px neměl vodorovné přetečení. Stažený text je místní soubor; uživatel může dříve staženou kopii nadále uchovat.

Aktualizováno 30. 10. 2026. Testováno na Windows s Pythonem 3.13.17 a místním serverem.

## Automatizované kontroly

`python -m unittest discover -s test -v`: **13/13 testů prošlo**. Testy pokrývají přesné počty, součet částek a zdrojové řádky, filtr zákazníka, nejednoznačný název, viditelnost souborů a počtů podle role, přímé HTTP požadavky na nepovolené soubory, odmítnutí jiného originu a Host hlavičky, limit vstupu, autorizační filtr před AI a ověření doslovného citátu.

`python -m py_compile core.py ai.py server.py` a `node --check web/app.js` prošly.

## Ruční průchod

- Provozní role viděla 5 souborů a 15 objednávek. Dotaz na rok 2024 vrátil 12 záznamů (11 dokončených, 1 stornovanou), odkazy na CSV a řádky 2–13.
- Dotaz na Studio Javor vrátil 5 záznamů (4 dokončené, 1 stornovanou).
- Personální role viděla 4 soubory, nikoli objednávky. Dotaz na jejich počet vrátil HTTP 403 a žádný počet.
- Při změně role se vymaže dřívější odpověď, zdroje, dotaz i otevřený soubor; opožděná odpověď se v nové roli nezobrazí. Tato chyba byla objevena během prohlížečové kontroly a opravena.
- Skutečný AI dotaz na schválení nákupu nad 80 000 Kč vrátil ředitelku a vlastníka společnosti s doslovným citátem z povoleného dokumentu. Server ověřil, že citát ve zdroji opravdu je.
- Vedení vidělo všech 9 souborů. Kontrolní panel po doplnění součtu hodnoty objednávek vykázal **8/8** průchodů přímo v prohlížeči.
- Hlavní rozhraní bylo vizuálně zkontrolováno v prohlížeči i v mobilním viewportu 390 × 844 px. Mobilní průchod odhalil nevhodně zobrazený seznam složek; CSS bylo opraveno a náhled znovu zkontrolován.
- Po zjednodušení vizuálu bylo rozhraní znovu zkontrolováno na šířce 1440 px a 390 px. Nový střídmý styl se načetl bez chyby, dotaz na objednávky v roce 2024 vrátil 12, změna na personální roli vymazala starou odpověď, panel vedení vykázal 8/8 kontrol a mobilní stránka neměla vodorovné přetečení. Přepnutí sekce vrací stránku nahoru. Aktuální desktopový náhled je v `docs/preview.png`.

## Orientační rychlost

Na malé fiktivní sadě trvalo 1 000 sekvenčních SQL dotazů na počet objednávek přibližně 310 ms a 1 000 sekvenčních vyhledání dokumentů přibližně 1 201 ms. Nejde o produkční benchmark a měření nezahrnuje latenci externí AI služby.

## Bezpečnostní hranice

Oprávnění se používají před výběrem dokumentů i při jejich otevření. Chybné ID zdroje nebo neexistující doslovný citát vedou k odmítnutí AI odpovědi. Požadavky jsou omezené na 4 096 bajtů, místní `Host`/`Origin`, dvě souběžná AI volání a 20 AI volání za 24 hodin v běžícím procesu. JSON API používá hlavičky CSP a `nosniff`; vstupní text se v klientu zobrazuje přes `textContent`.

Výběr role bez hesla znamená, že tato ukázka nemůže chránit skutečná data. Není veřejně nasazená a její místní server nemá trvalou ochranu placeného API provozu při restartu. Doslovný citát potvrzuje výskyt textu, nikoli správnou interpretaci.

## Kontrola vyhledávání 31. 10. 2026

Čtrnáct serverových testů prošlo. Nový test ověřuje vyhledání slova pouze v obsahu dokumentu, zákaz hledání bez relace, filtr rolí a to, že výsledky obsahují pouze metadata. Vyhledávání čte povolené dokumenty jedním SQL dotazem. Prohlížeč ověřil personální výsledek, přepnutí na provozní roli, vymazání starého hledání a mobilní šířku bez vodorovného přetečení. Přepnutí role okamžitě skryje předchozí seznam souborů a zastaví rozpracované hledání.

Místní orientační měření po změně: 1 000 sekvenčních vyhledání přibližně 391 ms (stejný malý fiktivní dataset). Srovnání se starším měřením 1 201 ms je orientační; nešlo o řízený výkonový experiment.


</details>
