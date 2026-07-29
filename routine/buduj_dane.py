#!/usr/bin/env python3
"""Wyłuskaj z wydań i raportów dane dla stron pochodnych (szukaj / angielski / kalendarz).

    python3 routine/buduj_dane.py

Jedno przejście po `wydania/*.html` i `raport-finansowy/*.md` produkuje trzy pliki
w `dane/`, z których korzystają statyczne strony:

    dane/szukaj.json     — wszystkie artykuły (tytuł, skrót, kategoria, kotwica)
    dane/angielski.json  — rubryka „Angielski na dziś” z każdego wydania
    dane/kalendarz.json  — wątki gazety + „Co obserwować” z raportów, po terminach

Wołany przez `buduj_index.py`, więc odświeża się przy każdej publikacji — rutyna
wykonuje jedno polecenie i nie ma jak o tym zapomnieć.
"""
import datetime
import json
import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parent.parent
DANE = REPO / "dane"

MIESIACE = {
    'stycznia': 1, 'styczeń': 1, 'styczen': 1,
    'lutego': 2, 'luty': 2,
    'marca': 3, 'marzec': 3,
    'kwietnia': 4, 'kwiecień': 4, 'kwiecien': 4,
    'maja': 5, 'maj': 5,
    'czerwca': 6, 'czerwiec': 6,
    'lipca': 7, 'lipiec': 7,
    'sierpnia': 8, 'sierpień': 8, 'sierpien': 8,
    'września': 9, 'wrzesień': 9, 'wrzesnia': 9, 'wrzesien': 9,
    'października': 10, 'październik': 10, 'pazdziernika': 10, 'pazdziernik': 10,
    'listopada': 11, 'listopad': 11,
    'grudnia': 12, 'grudzień': 12, 'grudzien': 12,
}
MIESIACE_PL = ['', 'stycznia', 'lutego', 'marca', 'kwietnia', 'maja', 'czerwca',
               'lipca', 'sierpnia', 'września', 'października', 'listopada', 'grudnia']
MIESIACE_MIAN = ['', 'styczeń', 'luty', 'marzec', 'kwiecień', 'maj', 'czerwiec',
                 'lipiec', 'sierpień', 'wrzesień', 'październik', 'listopad', 'grudzień']


# ------------------------------------------------------------------ pomoce ---

def bez_markdownu(s: str) -> str:
    """Zdejmij z tekstu formatowanie: **bold**, *kursywę*, `kod`, [link](url)."""
    s = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', s)
    s = re.sub(r'[*`]+', '', s)
    return re.sub(r'\s+', ' ', s).strip()


def parsuj_termin(tekst: str, kontekst: datetime.date):
    """Wyłuskaj datę z ludzkiego opisu terminu. Zwraca (ISO albo None, etykieta, przybliżony).

    Rozpoznaje `31.07.2026`, `31.07`, `2026-07-31`, `5 sierpnia [2026]`, `dziś`/`jutro`
    względem daty publikacji, a także sam miesiąc (`sierpień 2026`, `Q3 2026
    (sierpień/wrzesień)`) — ten ostatni jako termin PRZYBLIŻONY, przypięty do
    pierwszego dnia miesiąca. Czego nie rozpozna, ląduje w kalendarzu jako pozycja
    „bez daty” — lepsze to niż zmyślony termin."""
    t = (tekst or "").lower()
    przyblizony = False
    nazwy = '|'.join(MIESIACE)

    m = re.search(r'(\d{4})-(\d{2})-(\d{2})', t)
    if m:
        rok, mies, dzien = map(int, m.groups())
    elif (m := re.search(r'\b(\d{1,2})\.(\d{1,2})\.(\d{4})\b', t)):
        dzien, mies, rok = int(m.group(1)), int(m.group(2)), int(m.group(3))
    elif (m := re.search(r'\b(\d{1,2})\.(\d{1,2})\b(?!\.)', t)):
        dzien, mies, rok = int(m.group(1)), int(m.group(2)), kontekst.year
    elif (m := re.search(r'\b(\d{1,2})\s+(' + nazwy + r')\b', t)):
        dzien, mies = int(m.group(1)), MIESIACE[m.group(2)]
        rok_m = re.search(r'\b(20\d{2})\b', t)
        rok = int(rok_m.group(1)) if rok_m else kontekst.year
    elif 'jutro' in t:
        d = kontekst + datetime.timedelta(days=1)
        dzien, mies, rok = d.day, d.month, d.year
    elif 'dziś' in t or 'dzis' in t or 'dzisiaj' in t:
        dzien, mies, rok = kontekst.day, kontekst.month, kontekst.year
    elif (m := re.search(r'\b(' + nazwy + r')\b', t)):
        # sam miesiąc — przybliżenie do pierwszego dnia, etykieta zostaje słowna
        dzien, mies, przyblizony = 1, MIESIACE[m.group(1)], True
        rok_m = re.search(r'\b(20\d{2})\b', t)
        rok = int(rok_m.group(1)) if rok_m else kontekst.year
    else:
        return None, bez_markdownu(tekst), False

    try:
        d = datetime.date(rok, mies, dzien)
    except ValueError:
        return None, bez_markdownu(tekst), False
    # Termin bez roku, który wypadł mocno w tyle, dotyczy zwykle przyszłego roku.
    if (kontekst - d).days > 200:
        try:
            d = d.replace(year=d.year + 1)
        except ValueError:
            pass
    if przyblizony:
        return d.isoformat(), f"{MIESIACE_MIAN[d.month]} {d.year}", True
    return d.isoformat(), f"{d.day} {MIESIACE_PL[d.month]} {d.year}", False


def dane_wydania(plik: pathlib.Path):
    m = re.search(r'<script id="dane-gazety"[^>]*>(.*?)</script>',
                  plik.read_text(encoding='utf-8'), re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return None


def data_wydania(plik: pathlib.Path):
    m = re.match(r'(\d{4}-\d{2}-\d{2})-(rano|wieczor)', plik.stem)
    return datetime.date.fromisoformat(m.group(1)) if m else None


# ------------------------------------------------------------------ zbiory ---

def zbierz(wydania: list, raporty: list) -> dict:
    """Artykuły i angielski z CAŁEGO archiwum, kalendarz tylko z najnowszych źródeł.

    Obie rutyny same pielęgnują swoje listy terminów: gazeta przepisuje otwarte
    `watki` do kolejnego wydania, raport przenosi niezamknięte pozycje do sekcji
    „Co obserwować”. Najnowsze wydanie i najnowszy raport są więc pełnym, aktualnym
    stanem obserwacji — sięganie głębiej dokładałoby wyłącznie duplikaty tego samego
    terminu i pozycje, które redakcja świadomie porzuciła."""
    artykuly, angielski, kalendarz = [], [], []
    zrodla_kalendarza = set(p.name for p, _ in wydania[-1:]) | set(p.name for p, _, _ in raporty[-1:])

    for plik, dane in wydania:
        data = data_wydania(plik)
        if not data:
            continue
        etykieta = ('poranne' if '-rano' in plik.stem else 'wieczorne')
        opis_wydania = f"{data.day} {MIESIACE_PL[data.month]} {data.year}, wydanie {etykieta}"

        for i, a in enumerate(dane.get('artykuly') or []):
            artykuly.append({
                'tytul': a.get('tytul', ''),
                'skrot': a.get('skrot', ''),
                'kategoria': a.get('kategoria', ''),
                'data': data.isoformat(),
                'wydanie': f'wydania/{plik.name}#art-{i}',
                'opis_wydania': opis_wydania,
                'zrodlo': ((a.get('zrodlo') or {}).get('nazwa') or ''),
            })

        ang = (dane.get('literatura') or {}).get('angielski')
        if ang and ang.get('slowo'):
            wpis = {k: ang.get(k, '') for k in
                    ('slowo', 'wymowa', 'znaczenie', 'przyklad',
                     'zwrot', 'zwrot_znaczenie', 'zwrot_przyklad')}
            wpis['data'] = data.isoformat()
            wpis['wydanie'] = f'wydania/{plik.name}'
            wpis['opis_wydania'] = opis_wydania
            angielski.append(wpis)

        if plik.name not in zrodla_kalendarza:
            continue
        for w in dane.get('watki') or []:
            if isinstance(w, dict):
                iso, przyblizony = w.get('data') or None, False
                opis = ' — '.join(x for x in (w.get('temat'), w.get('sprawdzic')) if x)
                etykieta_terminu = ''
                if iso:
                    try:
                        d = datetime.date.fromisoformat(iso)
                        etykieta_terminu = f"{d.day} {MIESIACE_PL[d.month]} {d.year}"
                    except ValueError:
                        iso, etykieta_terminu = None, str(iso)
                else:
                    # bez pola `data` termin bywa opisany słownie w temacie
                    iso, etykieta_terminu, przyblizony = parsuj_termin(w.get('temat', ''), data)
            else:                                         # stary format: goły tekst
                # bywał poprzedzony technicznym slugiem („meta-q2-2026 — …”) — do kosza
                opis = re.sub(r'^[a-z0-9]+(?:-[a-z0-9]+){1,5}\s+[—–-]\s+', '',
                              bez_markdownu(str(w)))
                iso, etykieta_terminu, przyblizony = parsuj_termin(opis, data)
            if not opis:
                continue
            kalendarz.append({'data': iso, 'termin': etykieta_terminu, 'opis': opis,
                              'przyblizony': przyblizony, 'skad': 'Grzyb Times',
                              'opis_zrodla': opis_wydania, 'url': f'wydania/{plik.name}'})

    for plik, tresc, data in raporty:
        if plik.name not in zrodla_kalendarza:
            continue
        opis_zrodla = f"raport z {data.day} {MIESIACE_PL[data.month]} {data.year}"
        for termin, opis in obserwacje_z_raportu(tresc):
            iso, etykieta_terminu, przyblizony = parsuj_termin(termin, data)
            kalendarz.append({'data': iso, 'termin': etykieta_terminu or bez_markdownu(termin),
                              'opis': opis, 'przyblizony': przyblizony,
                              'skad': 'Raport finansowy', 'opis_zrodla': opis_zrodla,
                              'url': f'raport-finansowy/{plik.stem}.html'})

    # Wewnątrz jednego źródła ten sam termin bywa wpisany dwa razy — zostaw pierwszy.
    widziane, unikalne = set(), []
    for poz in kalendarz:
        klucz = (poz['data'], poz['opis'][:50].lower())
        if klucz in widziane:
            continue
        widziane.add(klucz)
        unikalne.append(poz)
    unikalne.sort(key=lambda p: (p['data'] is None, p['data'] or ''))

    return {'artykuly': artykuly, 'angielski': angielski, 'kalendarz': unikalne}


def obserwacje_z_raportu(tresc: str):
    """Pary (termin, opis) z sekcji „Co obserwować” raportu — tabela albo lista."""
    m = re.search(r'^#{2,4}\s*[^\n]*Co\s+obserwowa[ćc][^\n]*\n(.*?)(?=^#{1,4}\s|\Z)',
                  tresc, re.S | re.M | re.I)
    if not m:
        return []
    blok, wynik = m.group(1), []
    for linia in blok.split('\n'):
        linia = linia.strip()
        if not linia or linia.startswith('---'):
            continue
        if linia.startswith('|'):
            komorki = [c.strip() for c in linia.strip('|').split('|')]
            if len(komorki) < 2 or re.fullmatch(r'[\s:|-]+', linia.strip('|')):
                continue
            termin = bez_markdownu(komorki[0])
            if termin.lower() in ('termin', 'data', 'kiedy'):
                continue                                  # wiersz nagłówka tabeli
            opis = ' — '.join(bez_markdownu(c) for c in komorki[1:3] if c.strip())
            if termin and opis:
                wynik.append((termin, opis))
        elif linia.startswith(('-', '*')):
            punkt = bez_markdownu(linia.lstrip('-* '))
            czesci = re.split(r'\s+[—–-]\s+', punkt, maxsplit=1)
            if len(czesci) == 2:
                wynik.append((czesci[0], czesci[1]))
    return wynik


def main() -> None:
    wydania = []
    for plik in sorted((REPO / 'wydania').glob('*.html')):
        dane = dane_wydania(plik)
        if dane:
            wydania.append((plik, dane))

    raporty = []
    for plik in sorted((REPO / 'raport-finansowy').glob('*.md')):
        tresc = plik.read_text(encoding='utf-8')
        m = re.search(r'^date:\s*(\d{4}-\d{2}-\d{2})', tresc[:800], re.M)
        try:
            data = datetime.date.fromisoformat(m.group(1) if m else plik.stem[:10])
        except ValueError:
            continue
        raporty.append((plik, tresc, data))

    zbior = zbierz(wydania, raporty)
    DANE.mkdir(exist_ok=True)
    zbudowano = datetime.date.today().isoformat()
    for nazwa, klucz in (('szukaj', 'artykuly'), ('angielski', 'angielski'),
                         ('kalendarz', 'kalendarz')):
        (DANE / f'{nazwa}.json').write_text(
            json.dumps({'zbudowano': zbudowano, klucz: zbior[klucz]},
                       ensure_ascii=False, separators=(',', ':')),
            encoding='utf-8')

    print(f"dane/ OK — artykuły: {len(zbior['artykuly'])}, "
          f"angielski: {len(zbior['angielski'])}, kalendarz: {len(zbior['kalendarz'])}")


if __name__ == '__main__':
    main()
