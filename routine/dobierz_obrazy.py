#!/usr/bin/env python3
"""Dobierz grafiki źródeł (og:image) do świeżo opublikowanego wydania.

    python3 routine/dobierz_obrazy.py wydania/2026-07-30-rano-0352.html [--dry]

Po co osobny skrypt: środowisko rutyny siedzi za proxy, które przepuszcza tylko
GitHuba i API Anthropic, więc warstwa og:image nie pobrała ani jednej grafiki od
20.07.2026 (0/300 artykułów). GitHub Actions ma pełny internet, ale nie ma modelu —
więc robi dokładnie tę mechaniczną część, której rutyna nie dosięga, kilka minut
po publikacji.

ZABEZPIECZENIE: skrypt tyka WYŁĄCZNIE najnowsze wydanie w `wydania/`. Wydania
archiwalne są nietykalne (patrz README) — na starszy plik odpowiada odmową, a nie
błędem, żeby nie wywracać workflow.
"""
import json
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from buduj_wydanie import pobierz_og_image               # noqa: E402

# Dane wydania siedzą w bloku <script id="dane-gazety" type="application/json">,
# wypisane z indent=2. Podmieniamy wyłącznie środek bloku, więc reszta pliku
# zostaje bajt w bajt.
BLOK = re.compile(r'(<script id="dane-gazety"[^>]*>\s*\n)(.*?)(\n\s*</script>)', re.S)
NAZWA = re.compile(r'^(\d{4}-\d{2}-\d{2})-(rano|wieczor)(?:-\d{4})?$')


def najnowsze_wydanie():
    pliki = sorted((REPO / 'wydania').glob('*.html'))
    return pliki[-1] if pliki else None


def dobierz(plik: pathlib.Path, dry: bool) -> bool:
    """Uzupełnij grafiki w jednym wydaniu. Zwraca True, gdy plik został zmieniony."""
    najnowsze = najnowsze_wydanie()
    if not najnowsze or plik.resolve() != najnowsze.resolve():
        print(f"POMIJAM {plik.name} — to nie jest najnowsze wydanie "
              f"({najnowsze.name if najnowsze else 'brak wydań'}); archiwum jest nietykalne.")
        return False

    m_nazwa = NAZWA.match(plik.stem)
    if not m_nazwa:
        print(f"POMIJAM {plik.name} — nazwa nie wygląda na wydanie.")
        return False

    html = plik.read_text(encoding='utf-8')
    m = BLOK.search(html)
    if not m:
        print(f"POMIJAM {plik.name} — nie znalazłem bloku danych wydania.")
        return False
    try:
        dane = json.loads(m.group(2))
    except json.JSONDecodeError as ex:
        print(f"POMIJAM {plik.name} — dane wydania nie są poprawnym JSON-em ({ex}).")
        return False

    artykuly = dane.get('artykuly') or []
    brakuje = [a for a in artykuly if not (a.get('obraz') or {}).get('plik')]
    print(f"{plik.name}: {len(artykuly)} artykułów, bez grafiki: {len(brakuje)}")
    if not brakuje:
        print("  Komplet — nic do roboty.")
        return False

    if dry:
        for a in brakuje:
            print(f"  pobrałbym: {(a.get('zrodlo') or {}).get('url', '—')[:100]}")
        return False

    prefix = f"{m_nazwa.group(1)}-{m_nazwa.group(2)}"
    wpisy = []
    pobierz_og_image(artykuly, REPO / 'wydania' / 'img' / prefix, prefix,
                     lambda poziom, wiadomosc: wpisy.append(
                         {"poziom": poziom, "wiadomosc": wiadomosc}),
                     kontekst=" Dobrane po publikacji przez GitHub Actions.")

    nowe = sum(1 for a in artykuly if (a.get('obraz') or {}).get('plik'))
    if nowe == 0:
        print("  Nie udało się pobrać żadnej grafiki — plik zostaje bez zmian.")
        return False

    dane.setdefault('logi', []).extend(wpisy)
    tresc = html[:m.start(2)] + json.dumps(dane, ensure_ascii=False, indent=2) + html[m.end(2):]
    json.loads(BLOK.search(tresc).group(2))               # kontrola: nadal poprawny JSON
    plik.write_text(tresc, encoding='utf-8')
    print(f"  Zapisano — grafiki ze źródeł: {nowe}/{len(artykuly)}")
    return True


def main() -> None:
    argumenty = [a for a in sys.argv[1:] if not a.startswith('--')]
    dry = '--dry' in sys.argv[1:]
    if not argumenty:
        najnowsze = najnowsze_wydanie()
        if not najnowsze:
            sys.exit("Brak wydań w wydania/.")
        argumenty = [str(najnowsze)]

    zmienione = 0
    for sciezka in argumenty:
        plik = pathlib.Path(sciezka)
        if not plik.is_absolute():
            plik = REPO / sciezka
        if not plik.exists():
            print(f"POMIJAM {sciezka} — nie ma takiego pliku.")
            continue
        zmienione += dobierz(plik, dry)

    print(f"Zmienionych wydań: {zmienione}")


if __name__ == '__main__':
    main()
