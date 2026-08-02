#!/usr/bin/env python3
"""
Ripristina il fetch diretto dalle fonti pubbliche ufficiali di uBlock Origin,
senza passare dal proxy di Helium (che resta disattivato via pref).
"""
import json
import shutil
import sys
from pathlib import Path

# Mappa: path locale (asset bundlato) -> URL pubblico ufficiale da usare come
# fallback remoto, per riattivare gli aggiornamenti autonomi.
KNOWN_REMOTE_SOURCES = {
    "assets/assets.json":
        "https://raw.githubusercontent.com/gorhill/uBlock/master/assets/assets.json",
    "assets/thirdparties/publicsuffix.org/list/effective_tld_names.dat":
        "https://publicsuffix.org/list/public_suffix_list.dat",
    "assets/ublock/badlists.txt":
        "https://ublockorigin.github.io/uAssets/filters/badlists.txt",
    "assets/ublock/filters.txt":
        "https://ublockorigin.github.io/uAssets/filters/filters.txt",
    "assets/ublock/badware.txt":
        "https://ublockorigin.github.io/uAssets/filters/badware.txt",
    "assets/ublock/privacy.txt":
        "https://ublockorigin.github.io/uAssets/filters/privacy.txt",
    # Liste custom di Helium: sono su GitHub pubblico (raw.githubusercontent.com),
    # NON sul proxy services.helium.imput.net -> restano indipendenti da Helium
    # come infrastruttura, quindi le ripristiniamo comunque.
    "assets/helium/annoyances.txt":
        "https://raw.githubusercontent.com/imputnet/helium-services/main/filters/helium-annoyances.txt",
    "assets/helium/unbreak.txt":
        "https://raw.githubusercontent.com/imputnet/helium-services/main/filters/helium-unbreak.txt",
}

def fix_entry(key, entry, report):
    changed = False

    # Riattiva i CDN/patch pubblici disattivati con il prefisso "^"
    for disabled_key in ("^cdnURLs", "^patchURLs"):
        if disabled_key in entry:
            real_key = disabled_key.lstrip("^")
            entry[real_key] = entry.pop(disabled_key)
            report.append(f"  [{key}] riattivato: {disabled_key} -> {real_key}")
            changed = True

    # Ripristina contentURL remoto se manca e conosciamo la fonte ufficiale
    if "contentURL" in entry and isinstance(entry["contentURL"], list):
        urls = entry["contentURL"]
        has_remote = any(u.startswith("http") for u in urls)
        if not has_remote:
            for local_path in urls:
                if local_path in KNOWN_REMOTE_SOURCES:
                    remote = KNOWN_REMOTE_SOURCES[local_path]
                    entry["contentURL"] = [remote] + urls
                    report.append(f"  [{key}] aggiunto contentURL remoto: {remote}")
                    changed = True
                    break
            else:
                report.append(f"  [{key}] ATTENZIONE: nessuna fonte nota per {urls}")

    return changed

def main():
    if len(sys.argv) != 2:
        print("Uso: python3 fix_ublock_assets.py <path/to/assets.json>")
        sys.exit(1)

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"ERRORE: file non trovato: {path}")
        sys.exit(1)

    backup = path.with_suffix(path.suffix + ".bak")
    shutil.copy2(path, backup)
    print(f"Backup creato: {backup}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    report = []
    total_changed = 0
    for key, entry in data.items():
        if isinstance(entry, dict):
            if fix_entry(key, entry, report):
                total_changed += 1

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent="\t", ensure_ascii=False)
        f.write("\n")

    print(f"\n{len(report)} modifiche applicate su {total_changed} entry:")
    for line in report:
        print(line)

if __name__ == "__main__":
    main()
