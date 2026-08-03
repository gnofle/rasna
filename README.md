# Rasna Browser

**Rasna** è un browser web per Linux basato su [Helium](https://github.com/imputnet/helium) (a sua volta fork di ungoogled-chromium/Chromium), pensato per essere completamente indipendente dall'infrastruttura di rete di imputnet, con impostazioni predefinite orientate alla privacy.

- **Homepage progetto**: [www.gnofle.it/software/Rasna](https://www.gnofle.it/software/Rasna)
- **Repository**: [github.com/gnofle/rasna](https://github.com/gnofle/rasna)
- **Contatto**: software@gnofle.it
- **Proprietario / Maintainer**: Gnofle — ABGnofle Software

---

## Caratteristiche principali

- **Motore di ricerca e homepage predefiniti**: [DuckDuckGo](https://www.duckduckgo.com)
- **Indipendenza dai servizi Helium**: aggiornamenti browser, telemetria, proxy estensioni, spellcheck remoto e bangs sono disattivati di default — Rasna non contatta l'infrastruttura di imputnet
- **uBlock Origin integrato**: aggiorna le liste filtri direttamente dalle fonti pubbliche ufficiali (EasyList, uBlockOrigin/uAssets), non da alcun proxy di terzi
- **Widevine CDM funzionante**: supporto DRM (Netflix e altri servizi di streaming) tramite download diretto e legittimo dai server ufficiali Google, nessuna redistribuzione di componenti proprietari
- **Schema URL dedicato**: `rasna://` al posto di `chrome://`/`helium://`
- **Branding completo**: logo, icone (barra indirizzi, tab, New Tab Page, dock), copyright e versione personalizzati
- **Onboarding disattivato**: nessuna schermata di configurazione al primo avvio
- **Build monolitica ottimizzata**: binario singolo (~600 MB), nessuna dipendenza da librerie Chromium esterne oltre a quelle di sistema standard

---

## Struttura del repository

```
rasna/
├── patches/              # Patch in formato GNU quilt (ungoogled-chromium, iridium,
│                         # bromite, inox, brave, upstream-fixes, debian, helium)
├── resources/            # Asset di branding (loghi, favicon, icone .icon vettoriali)
├── utils/                # Script Python di build (clone, download, patch, rebranding)
├── devutils/             # Strumenti di sviluppo e validazione patch
├── logo/                 # Sorgenti del logo (PNG, tracciati vettoriali, varianti)
├── packaging/            # Struttura per il pacchetto Debian (.deb)
│   ├── debian/           # control, rules, changelog, copyright, postinst/postrm
│   ├── initial_preferences
│   └── rasna.desktop
├── fix_ublock_assets.py  # Script per ripristinare le fonti pubbliche di uBlock Origin
├── flags.gn               # Flag di configurazione GN per il build
├── deps.ini / downloads.ini
└── domain_substitution.list / domain_regex.list
```

---

## Compilare Rasna da sorgente

### Prerequisiti

- Linux (testato su GnofLinux / derivate Ubuntu-Debian)
- **~230 GB** di spazio libero su disco (sorgenti Chromium + build)
- **16 GB di RAM consigliati** (con meno RAM, usare `-j 2` o `-j 1` con ninja e disattivare la sospensione automatica del sistema)
- `git`, `python3`, `ninja`, `gn`
- [`depot_tools`](https://chromium.googlesource.com/chromium/tools/depot_tools.git) nel `PATH`
- ImageMagick (`convert`) e `potrace`, solo se si vogliono rigenerare gli asset del logo

```bash
git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git
export PATH="$(pwd)/depot_tools:$PATH"
```

### 1. Clonare il repository Rasna

```bash
git clone https://github.com/gnofle/rasna.git
cd rasna
```

### 2. Scaricare il sorgente Chromium

```bash
python3 utils/clone.py -o ../rasna_src -p linux -s amd64
```

### 3. Scaricare le dipendenze aggiuntive (dati motori di ricerca, onboarding, uBlock Origin)

```bash
mkdir -p ../rasna_downloads_cache
python3 utils/downloads.py retrieve -i deps.ini -c ../rasna_downloads_cache
python3 utils/downloads.py unpack -i deps.ini -c ../rasna_downloads_cache ../rasna_src
```

### 4. Applicare le patch

```bash
python3 utils/patches.py apply ../rasna_src patches/
```

### 5. Rebranding testuale dell'intero albero Chromium

Sostituisce ogni occorrenza di "Chrome"/"Chromium" con "Rasna" in tutte le stringhe di interfaccia (`.grd`/`.xtb`), oltre a quanto già gestito dalle patch dedicate.

```bash
python3 utils/name_substitution.py --sub -t ../rasna_src --backup-path /tmp/rasna_name_sub_backup.tar.gz
```

### 6. Applicare gli asset di branding (logo, favicon, icone)

```bash
python3 utils/generate_resources.py resources/generate_resources.txt resources
python3 utils/replace_resources.py resources/helium_resources.txt resources ../rasna_src
```

### 7. Ripristinare le fonti pubbliche di uBlock Origin

```bash
python3 fix_ublock_assets.py ../rasna_src/third_party/ublock/assets/assets.json
```

### 8. Scaricare i toolchain di build (Rust, Clang, Node.js, esbuild, gperf)

```bash
cd ../rasna_src

# Rust (versione ed hash esatti in DEPS)
mkdir -p third_party/rust-toolchain
curl -L -o /tmp/rust-toolchain.tar.xz "URL_DA_DEPS"
tar -xf /tmp/rust-toolchain.tar.xz -C third_party/rust-toolchain/

# Clang (script ufficiale, gestisce automaticamente la revisione corretta)
python3 tools/clang/scripts/update.py

# Node.js
bash third_party/node/update_node_binaries

# esbuild e gperf (pacchetti CIPD)
cipd install infra/3pp/tools/esbuild/linux-amd64 version:3@0.25.1.chromium.2 \
  -root third_party/devtools-frontend/src/third_party/esbuild
cipd install infra/3pp/tools/gperf/linux-amd64 version:3@3.2 \
  -root third_party/gperf/cipd
```

> I valori esatti di versione/hash per Rust vanno letti dal file `DEPS` alla voce `src/third_party/rust-toolchain`, che cambia periodicamente insieme alla versione di Chromium.

### 9. Configurare e compilare

```bash
mkdir -p out/Release
cat > out/Release/args.gn << 'EOF'
chrome_pgo_phase=0
clang_use_chrome_plugins=false
disable_fieldtrial_testing_config=true
enable_hangout_services_extension=false
enable_mdns=false
enable_remoting=false
enable_reporting=false
enable_service_discovery=false
enable_widevine=true
exclude_unwind_tables=true
google_api_key=""
google_default_client_id=""
google_default_client_secret=""
safe_browsing_mode=0
treat_warnings_as_errors=false
use_official_google_api_keys=false
use_unofficial_version_number=false
is_component_build=false
is_debug=false
symbol_level=0
blink_symbol_level=0
EOF

gn gen out/Release
ninja -j 2 -C out/Release chrome
```

> Su sistemi con poca RAM, `-j 2` (o anche `-j 1`) evita che il linking finale saturi RAM/swap. Il build completo richiede diverse ore; si consiglia di lanciarlo dentro `tmux` o `screen` e di disattivare la sospensione automatica del sistema:
> ```bash
> gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type 'nothing'
> ```

### 10. Testare il binario

```bash
./out/Release/chrome --user-data-dir=/tmp/rasna-test
```

---

## Creare il pacchetto Debian (.deb)

Con il build completato in `out/Release/`:

```bash
cd packaging
dpkg-buildpackage -us -uc -b
```

Il pacchetto `rasna_<versione>_amd64.deb` viene generato nella cartella superiore. Installazione:

```bash
sudo dpkg -i rasna_1.0.0-1_amd64.deb
sudo apt install -f   # risolve eventuali dipendenze mancanti
```

`debian/rules` fa riferimento al percorso assoluto dell'albero di build (`RASNA_SRC`) — aggiornarlo se la posizione dei sorgenti differisce da quella predefinita (`/media/gnofle/Dati/temp/rasna_src/out/Release`).

### File runtime necessari

Oltre al binario `chrome`, il pacchetto include: `chrome_100_percent.pak`, `chrome_200_percent.pak`, `resources.pak`, `icudtl.dat`, `v8_context_snapshot.bin`, `snapshot_blob.bin`, `chrome_crashpad_handler`, `libvulkan.so.1`, `libvk_swiftshader.so` + `vk_swiftshader_icd.json`, e le sole lingue italiano/inglese (`locales/it*.pak`, `locales/en-US*.pak`, `locales/en-GB.pak`) per contenere le dimensioni.

---

## Note tecniche e decisioni di progetto

- **Perché una build monolitica invece di component build**: la component build (`is_component_build=true`, usata di default in fase di sviluppo) produce centinaia di file `.so` separati, inadatta alla distribuzione. La build finale usa `is_component_build=false` per un binario singolo autosufficiente.
- **Perché i servizi Helium sono disattivati**: Helium instrada aggiornamenti, liste filtri uBlock e spellcheck attraverso un proxy proprio (`services.helium.imput.net`) per motivi di privacy. Rasna, non avendo un accordo con quell'infrastruttura, disattiva questi servizi e ripristina dove possibile il fetch diretto dalle fonti pubbliche ufficiali (uBlock Origin, Widevine/CRLSet via Google).
- **Widevine e CRLSet** sono gli unici due componenti ammessi dal component updater (whitelist in `components/component_updater/component_installer.cc`) e vengono scaricati direttamente da `update.googleapis.com`, esattamente come farebbe Chrome — nessuna redistribuzione di codice proprietario da parte di Rasna.
- **Rimane attivo** il blocco `trk:`/`qjz9zk` di ungoogled-chromium per il resto del traffico di tracciamento.

---

## Licenza

Rasna eredita la licenza **GPL-3.0** di Helium/ungoogled-chromium/Chromium. Vedi il file `LICENSE` nel repository.

Copyright © 2026 ABGnofle Software.

## Crediti

- [Helium](https://github.com/imputnet/helium) di imputnet
- [ungoogled-chromium](https://github.com/ungoogled-software/ungoogled-chromium)
- [Chromium](https://www.chromium.org/) di Google
- [uBlock Origin](https://github.com/gorhill/uBlock)
