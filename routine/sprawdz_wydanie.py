#!/usr/bin/env python3
"""Nocna kontrola opublikowanych wydań: spójność plików + czy linki źródeł żyją.

    python3 routine/sprawdz_wydanie.py [--wydania 3] [--issue]

Ten skrypt niczego nie naprawia i niczego nie commituje — znajduje usterkę
i oddaje sprawę tam, gdzie jest model: z flagą `--issue` zakłada (albo aktualizuje)
jedno zgłoszenie `[Auto] Usterki w wydaniach`, a rutyna czyta otwarte issues
w KROK 0.5. Gdy usterki znikną, skrypt sam zamyka swoje zgłoszenie.

KLASYFIKACJA ODPOWIEDZI jest tu najważniejsza. HTTP 403 to NIE usterka: bloomberg,
phys.org czy sciencedaily blokują boty i zwracają 403 na sprawnym artykule.
Usterką jest 404, 410 i brak domeny — czyli link, który czytelnikowi nie otworzy
się również w przeglądarce.
"""
import argparse
import concurrent.futures
import json
import pathlib
import re
import subprocess
import sys
import urllib.error
import urllib.request

REPO = pathlib.Path(__file__).resolve().parent.parent
TYTUL_ISSUE = "[Auto] Usterki w wydaniach"
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                    '(KHTML, like Gecko) Chrome/126 Safari/537.36'}
BLOK = re.compile(r'<script id="dane-gazety"[^>]*>(.*?)</script>', re.S)


# ------------------------------------------------------------------ spójność ---

def sprawdz_spojnosc(wydania: list, index_html: str) -> list:
    """Usterki, które widać bez sieci — w każdym opublikowanym wydaniu."""
    usterki = []
    for plik, dane, surowy in wydania:
        if '__DANE__' in surowy:
            usterki.append((plik.name, "szablon nie podstawił danych (`__DANE__` w pliku)"))
        if 'DEMO-START' in surowy:
            usterki.append((plik.name, "w wydaniu został blok demo (Lorem Ipsum)"))
        if plik.name not in index_html:
            usterki.append((plik.name, "archiwum (index.html) nie linkuje tego wydania"))
        if not (dane.get('artykuly') or []):
            usterki.append((plik.name, "wydanie nie ma ani jednego artykułu"))
        for a in dane.get('artykuly') or []:
            sciezka = (a.get('obraz') or {}).get('plik')
            if sciezka and not (REPO / sciezka.lstrip('/')).exists():
                usterki.append((plik.name, f"brak pliku grafiki `{sciezka}` "
                                           f"(artykuł „{a.get('tytul', '')[:50]}”)"))
    return usterki


# --------------------------------------------------------------------- linki ---

def sprawdz_url(zadanie):
    """(wydanie, tytuł, url) → (…, status) gdzie status to liczba HTTP albo nazwa błędu."""
    wydanie, tytul, url = zadanie
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=15) as odp:
            return wydanie, tytul, url, odp.status
    except urllib.error.HTTPError as ex:
        return wydanie, tytul, url, ex.code
    except Exception as ex:
        return wydanie, tytul, url, type(ex).__name__


def martwy(status) -> bool:
    """Czy to usterka, którą zobaczy też czytelnik w przeglądarce.

    403/401 = blokada bota na sprawnej stronie (Bloomberg, phys.org) — pomijamy.
    5xx i timeouty bywają chwilowe — raportujemy osobno, nie jako usterkę."""
    return status in (404, 410, 'URLError', 'gaierror')


def zbierz_linki(wydania: list) -> list:
    zadania = []
    for plik, dane, _ in wydania:
        for a in dane.get('artykuly') or []:
            url = (a.get('zrodlo') or {}).get('url')
            if url:
                zadania.append((plik.name, a.get('tytul', ''), url))
            for z in a.get('zrodla_dodatkowe') or []:
                if z.get('url'):
                    zadania.append((plik.name, a.get('tytul', ''), z['url']))
    return zadania


# ------------------------------------------------------------------- issue -----

def gh(*args, wejscie=None):
    """Wywołanie `gh`. Brak narzędzia albo tokena to powód, żeby przebieg był
    czerwony — usterka zostałaby wtedy niezgłoszona — ale komunikat ma być
    czytelny, a nie stack trace."""
    try:
        return subprocess.run(['gh', *args], cwd=REPO, capture_output=True, text=True,
                              input=wejscie, timeout=60)
    except FileNotFoundError:
        sys.exit("Brak narzędzia `gh` — nie mam jak zgłosić usterki. "
                 "Uruchom bez --issue albo zainstaluj GitHub CLI.")
    except subprocess.TimeoutExpired:
        sys.exit("`gh` nie odpowiedział w 60 s — zgłoszenie nieutworzone.")


def otwarte_issue():
    wynik = gh('issue', 'list', '--state', 'open', '--json', 'number,title', '--limit', '50')
    if wynik.returncode != 0:
        print(f"  (gh issue list nieudane: {wynik.stderr.strip()[:120]})")
        return None
    try:
        for i in json.loads(wynik.stdout or '[]'):
            if i['title'] == TYTUL_ISSUE:
                return i['number']
    except json.JSONDecodeError:
        pass
    return None


def zglos(tresc: str | None) -> None:
    """Utrzymuje DOKŁADNIE jedno zgłoszenie: zakłada, aktualizuje albo zamyka."""
    numer = otwarte_issue()
    if tresc is None:
        if numer:
            gh('issue', 'close', str(numer), '--comment',
               'Wszystkie sprawdzane linki odpowiadają, wydania są spójne — zamykam.')
            print(f"  Zamknięto issue #{numer} — usterek już nie ma.")
        else:
            print("  Brak usterek, brak otwartego zgłoszenia — nic do roboty.")
        return
    if numer:
        gh('issue', 'edit', str(numer), '--body-file', '-', wejscie=tresc)
        print(f"  Zaktualizowano issue #{numer}.")
    else:
        wynik = gh('issue', 'create', '--title', TYTUL_ISSUE, '--body-file', '-', wejscie=tresc)
        print(f"  Założono zgłoszenie: {wynik.stdout.strip() or wynik.stderr.strip()[:160]}")


# -------------------------------------------------------------------- główne ---

def main() -> None:
    ap = argparse.ArgumentParser(description="Kontrola opublikowanych wydań.")
    ap.add_argument('--wydania', type=int, default=3,
                    help="ile najnowszych wydań sprawdzać pod kątem linków (domyślnie 3)")
    ap.add_argument('--issue', action='store_true',
                    help="zgłoś wynik jako issue na GitHubie (wymaga gh + GITHUB_TOKEN)")
    args = ap.parse_args()

    pliki = sorted((REPO / 'wydania').glob('*.html'))
    if not pliki:
        sys.exit("Brak wydań w wydania/.")
    index_html = (REPO / 'index.html').read_text(encoding='utf-8')

    wszystkie = []
    for plik in pliki:
        surowy = plik.read_text(encoding='utf-8')
        m = BLOK.search(surowy)
        if not m:
            wszystkie.append((plik, {}, surowy))
            continue
        try:
            wszystkie.append((plik, json.loads(m.group(1)), surowy))
        except json.JSONDecodeError as ex:
            print(f"  {plik.name}: dane wydania nie są poprawnym JSON-em ({ex})")
            wszystkie.append((plik, {}, surowy))

    print(f"Wydań w archiwum: {len(wszystkie)} | linki sprawdzam w {args.wydania} najnowszych")
    usterki = sprawdz_spojnosc(wszystkie, index_html)
    for nazwa, opis in usterki:
        print(f"  SPÓJNOŚĆ  {nazwa}: {opis}")

    zadania = zbierz_linki(wszystkie[-args.wydania:])
    print(f"Sprawdzam {len(zadania)} linków…")
    wyniki = []
    with concurrent.futures.ThreadPoolExecutor(8) as pula:
        for wynik in pula.map(sprawdz_url, zadania):
            wyniki.append(wynik)

    zle = [w for w in wyniki if martwy(w[3])]
    niepewne = [w for w in wyniki if not martwy(w[3]) and not (isinstance(w[3], int) and w[3] < 400)]
    dobre = len(wyniki) - len(zle) - len(niepewne)
    print(f"  odpowiada: {dobre} | martwe: {len(zle)} | zablokowane lub chwilowe: {len(niepewne)}")
    for wydanie, tytul, url, status in zle:
        print(f"  MARTWY    {status}  {wydanie}  {url[:90]}")

    if not args.issue:
        return

    if not usterki and not zle:
        zglos(None)
        return

    linie = ["Zgłoszenie automatyczne — kontrola opublikowanych wydań.", ""]
    if zle:
        linie += [f"## Martwe linki źródeł ({len(zle)})", "",
                  "| Wydanie | Status | Artykuł | Link |", "|---|---|---|---|"]
        linie += [f"| {w} | {s} | {t[:60]} | {u} |" for w, t, u, s in zle]
        linie += ["", "Serwis, który regularnie tu wraca, przestaje być wiarygodnym źródłem "
                      "— warto rozważyć usunięcie go z `zrodla_pierwotne` w `config.yaml`.", ""]
    if usterki:
        linie += [f"## Usterki spójności ({len(usterki)})", ""]
        linie += [f"- **{n}** — {o}" for n, o in usterki]
        linie += [""]
    linie += ["---", "", f"Sprawdzono {len(wyniki)} linków w {args.wydania} najnowszych wydaniach. "
                        f"HTTP 403 nie jest tu usterką — to blokada bota na sprawnej stronie.",
              "", "Zgłoszenie zamknie się samo, gdy problem zniknie."]
    zglos("\n".join(linie))


if __name__ == '__main__':
    main()
