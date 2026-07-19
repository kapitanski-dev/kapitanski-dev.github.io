#!/usr/bin/env python3
"""Czyszczenie starych wydań Grzyb Times.

Usuwa z `wydania/` pliki starsze niż --dni (wraz z ich katalogami grafik
`wydania/img/DATA-WYDANIE/`) i odbudowuje index.html tą samą logiką, której
używa rutyna (kod KROK 4 czytany wprost z routine/instrukcja.md — jedna
prawda, zero duplikacji).

Użycie:
    python3 routine/czysc_stare.py --dni 60          # usuń starsze niż 60 dni
    python3 routine/czysc_stare.py --dni 60 --dry    # tylko pokaż, co usunie
Potem: git add -A && git commit && git push
"""
import argparse
import datetime
import pathlib
import re
import shutil
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent


def main() -> None:
    ap = argparse.ArgumentParser(description="Usuń wydania starsze niż N dni.")
    ap.add_argument("--dni", type=int, default=60, help="próg wieku w dniach (domyślnie 60)")
    ap.add_argument("--dry", action="store_true", help="nic nie usuwaj, tylko wypisz")
    args = ap.parse_args()

    prog = datetime.date.today() - datetime.timedelta(days=args.dni)
    wydania = REPO / "wydania"
    usuniete = 0

    for f in sorted(wydania.glob("*.html")):
        m = re.match(r"(\d{4}-\d{2}-\d{2})-(rano|wieczor)", f.stem)
        if not m:
            continue
        data = datetime.date.fromisoformat(m.group(1))
        if data >= prog:
            continue
        imgdir = wydania / "img" / f"{m.group(1)}-{m.group(2)}"
        rozmiar = f.stat().st_size + sum(p.stat().st_size for p in imgdir.glob("*")) if imgdir.exists() else f.stat().st_size
        print(f"{'[DRY] ' if args.dry else ''}usuwam {f.name}"
              + (f" + {imgdir.relative_to(REPO)}" if imgdir.exists() else "")
              + f" ({rozmiar // 1024} KB)")
        if not args.dry:
            f.unlink()
            if imgdir.exists():
                shutil.rmtree(imgdir)
        usuniete += 1

    if usuniete == 0:
        print(f"Nic do usunięcia (próg: starsze niż {prog}).")
        return

    if args.dry:
        print(f"[DRY] Do usunięcia: {usuniete} wydań. Uruchom bez --dry, by usunąć.")
        return

    # Odbuduj index.html kodem KROK 4 z instrukcji (ta sama logika co rutyna).
    md = (REPO / "routine" / "instrukcja.md").read_text(encoding="utf-8")
    kod = re.search(r"## KROK 4.*?```python\n(.*?)```", md, re.S)
    if not kod:
        sys.exit("Nie znalazłem kodu KROK 4 w routine/instrukcja.md — index.html nieodświeżony.")
    exec(re.sub(
        r"REPO = subprocess\.run\(.*?\)\.stdout\.strip\(\)",
        f"REPO = {str(REPO)!r}",
        kod.group(1), count=1, flags=re.S,
    ))
    print(f"Usunięto {usuniete} wydań; index.html odbudowany. Teraz: git add -A && git commit && git push")


if __name__ == "__main__":
    main()
