# CompanyAtlas: video ukázka

**[Stáhnout MP4 — 1:26, bez zvuku](https://raw.githubusercontent.com/OmegaCatt/companyatlas/main/docs/videos/companyatlas.mp4)** · [Soubor na GitHubu](https://github.com/OmegaCatt/companyatlas/blob/main/docs/videos/companyatlas.mp4)

SQL odpovědi 12/5, zdrojové řádky, tři účty a přístupové kontroly.

## Co ve videu uvidíte

- SQL odpověď: 12 objednávek v roce 2024, z toho 5 pro Studio Javor.
- Otevření původních řádků a přihlášení k různým ukázkovým účtům.
- Personální podklad, odmítnutí přístupu k objednávkám a osm kontrol s očekáváním/skutečností.

Video zachycuje skutečnou aplikaci nad izolovanými fiktivními daty. Má rozlišení **1920 × 1080**, **25 snímků/s**, přibližně **10.2 MB** a české titulky přímo v obrazu. Pohyb myši i kliknutí jsou viditelné. **Neobsahuje zvukovou stopu.**

Odkaz stáhne video MP4. Po stažení jej otevřete v běžném přehrávači videa. Ukázka nepotřebuje instalaci aplikace. Pro vlastní vyzkoušení pokračujte [návodem ke spuštění](../README.md#spuštění-krok-za-krokem-windows).

## Jak byl záznam ověřen

Při pořizování proběhl skutečný HTTP/browser scénář s kontrolami výsledků. AI API nebylo volané. Ověřeno celé dekódování výsledného MP4, H.264/yuv420p, rozlišení, absence audio stopy, samostatné přehrání/posun a obrazové snímky titulkových úseků a kliknutí. Jde o ověření konkrétní ukázky; záznam neměří obecnou přesnost AI ani produkční připravenost aplikace.

[Metadata záznamu](videos/companyatlas-recording.json) obsahují kontrolované výsledky, zdrojový commit `25e9e8c3705156a868824616a99c172edb9f63a9` a otisky nahrávacích skriptů. SHA-256 MP4: `fc6485d60d211c8afcc29288a42ad1fc11240194d5e994a58c7bccd380b97808`. Časy kroků v metadatech jsou orientační; titulky jsou přímo v obrazu.

Scénář: [scripts/record-demo.mjs](../scripts/record-demo.mjs). Nahrávací vrstva: [scripts/recording.mjs](../scripts/recording.mjs). Při vývojovém zopakování je potřeba Playwright a plný FFmpeg s libx264 (`PORTFOLIO_FFMPEG`); běžné přehrání videa je nevyžaduje.

## English

**[Download the silent Full HD demo (1:26)](https://raw.githubusercontent.com/OmegaCatt/companyatlas/main/docs/videos/companyatlas.mp4).** Open the downloaded MP4 in a standard video player. Czech captions are burned into the image; the pointer and actual clicks are visible. Recorded from the real application using isolated fictional data, with result assertions and no AI API calls. Full decoding, playback, seeking and absence of audio were verified. [Run the application locally](../README.md#spuštění-krok-za-krokem-windows).
