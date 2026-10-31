# Ověření CompanyAtlas

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
