#!/usr/bin/env python3
"""Przebuduj index.html (archiwum wydań) logiką KROK 4 z routine/instrukcja.md.

Jedna prawda, zero duplikacji: kod budujący archiwum żyje w instrukcji (KROK 4),
a ten skrypt tylko go wyłuskuje i uruchamia dla bieżącego repo. Wołany
AUTOMATYCZNIE w KROK 5 publikacji — dzięki temu archiwum ZAWSZE linkuje świeżo
dodane wydanie (wpadka 24.07: wydanie poranne poszło bez wpisu w index.html, bo
KROK 4 został pominięty). Można też odpalić ręcznie: `python3 routine/buduj_index.py`.
"""
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent


def main() -> None:
    md = (REPO / "routine" / "instrukcja.md").read_text(encoding="utf-8")
    m = re.search(r"## KROK 4.*?```python\n(.*?)```", md, re.S)
    if not m:
        sys.exit("Nie znalazłem kodu KROK 4 w routine/instrukcja.md — index.html nieodświeżony.")
    # Podmień autodetekcję REPO (find po /home /root /workspace /tmp) na bieżące repo.
    kod = re.sub(
        r"REPO = subprocess\.run\(.*?\)\.stdout\.strip\(\)",
        f"REPO = {str(REPO)!r}",
        m.group(1), count=1, flags=re.S,
    )
    exec(kod, {})


if __name__ == "__main__":
    main()
