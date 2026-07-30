#!/usr/bin/env python3
"""Co w rubryce „Literatura” już było — lista zakazana dla kolejnego wydania.

    python3 routine/literatura_historia.py          # okno z config.yaml
    python3 routine/literatura_historia.py 10       # ostatnie 10 wydań

Rutyna startuje bez pamięci poprzednich przebiegów, a instrukcja każe składać rubrykę
„z własnej wiedzy” — efekt: model wraca do tych samych, najbardziej oczywistych pozycji
(audyt 30.07.2026: Kochanowski w 5 wierszach z 6, „Na zdrowie” i „Kuj żelazo, póki
gorące” po dwa razy w trzy dni, `resilience` dwa razy w trzy dni). Ten skrypt czyta
archiwum wydań i wypisuje, co jest zajęte — model dostaje pamięć w jednym tanim
wywołaniu, bez tokenów sieci.

Ten sam moduł woła `buduj_wydanie.py` (kontrola_literatury), więc powtórka nie
przechodzi przez sito po cichu, nawet jeśli rutyna pominie ten krok.
"""
import json
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
POLA = ('cytat', 'przyslowie', 'wiersz', 'angielski')


def _norm(s) -> str:
    """Do porównań: bez wielkości liter, interpunkcji i ogonków („Kuj żelazo, póki
    gorące.” == „kuj zelazo poki gorace”), żeby drobna przeróbka nie omijała kontroli."""
    s = (s or "").lower()
    for a, b in zip("ąćęłńóśźż", "acelnoszz"):
        s = s.replace(a, b)
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9]+', ' ', s)).strip()


def _wydania(ile: int) -> list:
    """Najnowsze `ile` wydań, od najświeższego (nazwa pliku = kolejność chronologiczna)."""
    pliki = sorted(p for p in (REPO / 'wydania').glob('*.html')
                   if re.match(r'\d{4}-\d{2}-\d{2}-(rano|wieczor)', p.stem))
    return list(reversed(pliki))[:ile]


def _literatura(plik: pathlib.Path) -> dict:
    m = re.search(r'<script id="dane-gazety"[^>]*>(.*?)</script>',
                  plik.read_text(encoding='utf-8'), re.S)
    if not m:
        return {}
    try:
        return (json.loads(m.group(1)).get('literatura') or {})
    except json.JSONDecodeError:
        return {}


def zebrane(ile: int = 30) -> list:
    """Historia rubryki: lista wpisów `{wydanie, cytat, przyslowie, wiersz, angielski}`
    od najnowszego wydania. Puste pola znaczą, że w tym wydaniu rubryki nie było."""
    historia = []
    for plik in _wydania(ile):
        lit = _literatura(plik)
        if not lit:
            continue
        historia.append({
            "wydanie": plik.stem,
            "cytat": (lit.get('cytat') or {}),
            "przyslowie": (lit.get('przyslowie') or {}),
            "wiersz": (lit.get('wiersz') or {}),
            "angielski": (lit.get('angielski') or {}),
        })
    return historia


def kolizje(literatura: dict, ile: int = 30, historia: list = None) -> list:
    """Powtórki nowej rubryki względem archiwum — lista gotowych komunikatów.

    Reguły (im bliżej wydania, tym ostrzej): ten sam wiersz, przysłowie, cytat, słowo
    lub zwrot nie może wrócić w oknie `ile` wydań, a AUTOR wiersza i cytatu nie może
    wrócić w oknie 10 wydań — powtórzony autor to ten sam problem co powtórzony utwór
    (pięć razy Kochanowski to nie „stała rubryka”, to koleina)."""
    historia = zebrane(ile) if historia is None else historia
    OKNO_AUTORA = 10
    problemy = []

    def rodzina(a: str, b: str) -> bool:
        """Ta sama rodzina słowa: `resilience` i `resilient` to dla czytelnika to samo
        słówko (były w wydaniach 25.07 i 27.07). Wspólny przedrostek 7 znaków wystarcza,
        by je złapać, a jest za długi, by mylić niezależne wyrazy."""
        wspolne = 0
        for x, y in zip(a, b):
            if x != y:
                break
            wspolne += 1
        return wspolne >= 7 and wspolne >= min(len(a), len(b)) - 3

    def szukaj(pole, klucz, wartosc, etykieta, okno=None, luzno=False):
        cel = _norm(wartosc)
        if not cel:
            return
        for i, h in enumerate(historia[:okno or len(historia)]):
            bylo = _norm((h.get(pole) or {}).get(klucz))
            if bylo == cel or (luzno and bylo and rodzina(bylo, cel)):
                problemy.append(f"{etykieta} „{str(wartosc)[:60]}” było już w wydaniu "
                                f"{h['wydanie']} ({i + 1}. wydanie wstecz)")
                return

    wiersz = literatura.get('wiersz') or {}
    szukaj('wiersz', 'tytul', wiersz.get('tytul'), 'Wiersz')
    szukaj('wiersz', 'autor', wiersz.get('autor'), 'Autor wiersza', OKNO_AUTORA)

    cytat = literatura.get('cytat') or {}
    szukaj('cytat', 'tresc', cytat.get('tresc'), 'Cytat')
    szukaj('cytat', 'autor', cytat.get('autor'), 'Autor cytatu', OKNO_AUTORA)

    szukaj('przyslowie', 'tresc', (literatura.get('przyslowie') or {}).get('tresc'), 'Przysłowie')

    ang = literatura.get('angielski') or {}
    szukaj('angielski', 'slowo', ang.get('slowo'), 'Słowo', luzno=True)
    szukaj('angielski', 'zwrot', ang.get('zwrot'), 'Zwrot')
    return problemy


def _okno_z_configu() -> int:
    m = re.search(r'^\s*bez_powtorek_wydan:\s*(\d+)',
                  (REPO / 'config.yaml').read_text(encoding='utf-8'), re.M)
    return int(m.group(1)) if m else 30


def main() -> None:
    ile = int(sys.argv[1]) if len(sys.argv) > 1 else _okno_z_configu()
    historia = zebrane(ile)
    if not historia:
        print("Archiwum puste — rubryka bez ograniczeń.")
        return

    print(f"ZAJĘTE w ostatnich {len(historia)} wydaniach (od najnowszego) — NIE POWTARZAJ:\n")
    wiersze = [(h['wiersz'].get('autor'), h['wiersz'].get('tytul')) for h in historia
               if h['wiersz'].get('tytul')]
    print("WIERSZE (utwór: nigdy więcej; autor: nie w 10 ostatnich wydaniach):")
    for autor, tytul in wiersze:
        print(f"  - {autor}: „{tytul}”")
    autorzy = [a for a, _ in wiersze[:10] if a]
    if autorzy:
        print(f"  → autorzy zablokowani teraz: {', '.join(dict.fromkeys(autorzy))}")

    print("\nCYTATY (autor: nie w 10 ostatnich wydaniach):")
    for h in historia:
        if h['cytat'].get('tresc'):
            print(f"  - {h['cytat'].get('autor')}: „{h['cytat']['tresc'][:70]}”")

    print("\nPRZYSŁOWIA:")
    for h in historia:
        if h['przyslowie'].get('tresc'):
            print(f"  - „{h['przyslowie']['tresc']}”")

    print("\nANGIELSKI (słowo / zwrot):")
    for h in historia:
        if h['angielski']:
            print(f"  - {h['angielski'].get('slowo')} / {h['angielski'].get('zwrot')}")


if __name__ == '__main__':
    main()
