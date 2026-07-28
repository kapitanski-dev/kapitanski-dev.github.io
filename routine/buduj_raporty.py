#!/usr/bin/env python3
"""Zbuduj strony raportów finansowych: raport-finansowy/*.md → *.html po `raport-template.html`.

Rutyna raportowa pisze **tylko markdown** (`raport-finansowy/RRRR-MM-DD-nazwa.md`
z front matterem `title:` / `date:`), a ten skrypt renderuje z niego stronę w
stylistyce gazety. Uruchamiany przed commitem:

    python3 routine/buduj_raporty.py            # wszystkie raporty
    python3 routine/buduj_raporty.py plik.md    # jeden konkretny

Konwerter markdownu jest celowo mały i bez zależności (`markdown` nie jest
zainstalowany w środowisku rutyn). Obsługuje to, czego raporty faktycznie
używają: nagłówki, akapity, **pogrubienie**, *kursywę*, `kod`, odnośniki,
listy punktowane i numerowane, cytaty blokowe, tabele GFM i poziome linie.
"""
import datetime
import html
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
KATALOG = REPO / "raport-finansowy"
SZABLON = REPO / "raport-template.html"

MIESIACE = ['', 'stycznia', 'lutego', 'marca', 'kwietnia', 'maja', 'czerwca',
            'lipca', 'sierpnia', 'września', 'października', 'listopada', 'grudnia']
DNI = ['poniedziałek', 'wtorek', 'środa', 'czwartek', 'piątek', 'sobota', 'niedziela']


# ---------------------------------------------------------------- markdown ---

def inline(s: str) -> str:
    """Formatowanie w linii. Kolejność ma znaczenie: escape → linki → bold → italic."""
    s = html.escape(s, quote=False)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    s = re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)',
               lambda m: f'<a href="{html.escape(m.group(2), quote=True)}" '
                         f'rel="noopener">{m.group(1)}</a>', s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'(?<![\w*])\*([^*\n]+)\*(?![\w*])', r'<em>\1</em>', s)
    return s


def komorki(wiersz: str) -> list:
    """Rozbij wiersz tabeli GFM na komórki (obcina zewnętrzne `|`)."""
    return [c.strip() for c in wiersz.strip().strip('|').split('|')]


def render(md: str) -> str:
    """Markdown → HTML. Blok po bloku, bez rekurencji poza cytatami."""
    linie = md.split('\n')
    out, i = [], 0
    while i < len(linie):
        ln = linie[i]

        if not ln.strip():
            i += 1
            continue

        # Pozioma linia
        if re.fullmatch(r'\s*([-*_])\1{2,}\s*', ln):
            out.append('<hr>')
            i += 1
            continue

        # Nagłówek
        m = re.match(r'\s*(#{1,6})\s+(.*)', ln)
        if m:
            poziom = len(m.group(1))
            out.append(f'<h{poziom}>{inline(m.group(2).strip())}</h{poziom}>')
            i += 1
            continue

        # Tabela: wiersz nagłówka + wiersz separatora (|---|---|)
        if ln.lstrip().startswith('|') and i + 1 < len(linie) \
                and re.fullmatch(r'\s*\|[\s:|-]+\|\s*', linie[i + 1]):
            naglowek = komorki(ln)
            i += 2
            wiersze = []
            while i < len(linie) and linie[i].lstrip().startswith('|'):
                wiersze.append(komorki(linie[i]))
                i += 1
            thead = ''.join(f'<th>{inline(c)}</th>' for c in naglowek)
            tbody = ''.join(
                '<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in w) + '</tr>'
                for w in wiersze)
            out.append('<div class="tabela"><table><thead><tr>' + thead
                       + '</tr></thead><tbody>' + tbody + '</tbody></table></div>')
            continue

        # Cytat blokowy
        if ln.lstrip().startswith('>'):
            blok = []
            while i < len(linie) and linie[i].lstrip().startswith('>'):
                blok.append(re.sub(r'^\s*>\s?', '', linie[i]))
                i += 1
            out.append('<blockquote>' + render('\n'.join(blok)) + '</blockquote>')
            continue

        # Lista punktowana / numerowana
        for wzor, tag in ((r'\s*[-*+]\s+(.*)', 'ul'), (r'\s*\d+[.)]\s+(.*)', 'ol')):
            if re.fullmatch(wzor, ln):
                punkty = []
                while i < len(linie) and re.fullmatch(wzor, linie[i]):
                    punkty.append(re.fullmatch(wzor, linie[i]).group(1).strip())
                    i += 1
                    # kontynuacja punktu w kolejnej, wciętej linii
                    while i < len(linie) and linie[i].startswith(('   ', '\t')) \
                            and linie[i].strip() and not re.fullmatch(wzor, linie[i]):
                        punkty[-1] += ' ' + linie[i].strip()
                        i += 1
                out.append(f'<{tag}>' + ''.join(f'<li>{inline(p)}</li>' for p in punkty)
                           + f'</{tag}>')
                break
        else:
            # Akapit — kolejne linie aż do pustej lub początku innego bloku
            akapit = []
            while i < len(linie) and linie[i].strip() \
                    and not re.match(r'\s*(#{1,6}\s|>|[-*+]\s|\d+[.)]\s|\|)', linie[i]) \
                    and not re.fullmatch(r'\s*([-*_])\1{2,}\s*', linie[i]):
                akapit.append(linie[i].strip())
                i += 1
            if akapit:
                out.append('<p>' + inline(' '.join(akapit)) + '</p>')
            else:
                i += 1
        continue

    return '\n'.join(out)


# ------------------------------------------------------------------ budowa ---

def front_matter(tekst: str):
    """Zwróć (dict front mattera, reszta dokumentu)."""
    m = re.match(r'﻿?---\s*\n(.*?)\n---\s*\n?(.*)', tekst, re.S)
    if not m:
        return {}, tekst
    meta = {}
    for linia in m.group(1).split('\n'):
        mm = re.match(r'\s*([A-Za-z_]+):\s*(.*)', linia)
        if mm:
            meta[mm.group(1)] = mm.group(2).strip().strip('"\'')
    return meta, m.group(2)


def zbuduj(plik: pathlib.Path, szablon: str, sasiedzi: dict) -> pathlib.Path:
    meta, tresc_md = front_matter(plik.read_text(encoding='utf-8'))

    data_str = meta.get('date', plik.stem[:10])
    try:
        d = datetime.date.fromisoformat(data_str)
    except ValueError:
        d = None
    data_txt = f'{DNI[d.weekday()]}, {d.day} {MIESIACE[d.month]} {d.year}' if d else data_str
    data_iso = f'{d.isoformat()}T12:00:00Z' if d else ''

    tytul = meta.get('title') or f'Przegląd rynku — {data_txt}'
    # H1 to sam temat: „Przegląd rynku – 28 lipca 2026 (wieczorne)” → „Przegląd rynku”,
    # bo datę pokazuje pasek pod nagłówkiem, a dopisek w nawiasie ląduje w kickerze.
    m_temat = re.match(r'^(.*?)\s*[–—-]\s*\d.*$', tytul)
    tytul_h1 = (m_temat.group(1) if m_temat else re.sub(r'\s*\([^)]*\)\s*$', '', tytul)).strip()
    m_dopisek = re.search(r'\(([^)]+)\)\s*$', tytul)
    kicker = 'Raport finansowy'
    if m_dopisek:
        kicker += ' &middot; ' + html.escape(m_dopisek.group(1), quote=False)

    # Pierwszy „# …” z markdownu dubluje nagłówek strony — usuwamy.
    tresc_md = re.sub(r'\A\s*#\s+[^\n]*\n', '', tresc_md)
    tresc = render(tresc_md)

    starszy, nowszy = sasiedzi.get('starszy'), sasiedzi.get('nowszy')
    nawigacja = (
        (f'<a href="/raport-finansowy/{starszy}">&larr; Poprzedni raport</a>'
         if starszy else '<span></span>')
        + '<span class="nav-spacer"></span><a href="/">Archiwum</a><span class="nav-spacer"></span>'
        + (f'<a href="/raport-finansowy/{nowszy}">Następny raport &rarr;</a>'
           if nowszy else '<span></span>')
    )

    strona = szablon
    for klucz, wartosc in (('__TYTUL_H1__', html.escape(tytul_h1, quote=False)),
                           ('__TYTUL__', html.escape(tytul, quote=False)),
                           ('__KICKER__', kicker),
                           ('__DATA_ISO__', data_iso),
                           ('__DATA__', data_txt),
                           ('__NAWIGACJA__', nawigacja),
                           ('__TRESC__', tresc)):
        strona = strona.replace(klucz, wartosc)

    cel = plik.with_suffix('.html')
    cel.write_text(strona, encoding='utf-8')
    return cel


def main() -> None:
    if not SZABLON.exists():
        sys.exit(f'Brak szablonu {SZABLON.name} — nie ma z czego budować raportów.')
    szablon = SZABLON.read_text(encoding='utf-8')

    # Kolejność jak w archiwum: najnowszy pierwszy (sąsiedzi = nawigacja na stronie).
    wszystkie = sorted(KATALOG.glob('*.md'), key=lambda p: p.stem, reverse=True)
    if not wszystkie:
        print('Brak raportów w raport-finansowy/ — nic do zbudowania.')
        return

    wybrane = wszystkie
    if len(sys.argv) > 1:
        chciane = {pathlib.Path(a).name for a in sys.argv[1:]}
        wybrane = [p for p in wszystkie if p.name in chciane]
        if not wybrane:
            sys.exit(f'Nie znalazłem w {KATALOG.name}/: {", ".join(sorted(chciane))}')

    for plik in wybrane:
        idx = wszystkie.index(plik)
        cel = zbuduj(plik, szablon, {
            'nowszy': wszystkie[idx - 1].with_suffix('.html').name if idx > 0 else None,
            'starszy': wszystkie[idx + 1].with_suffix('.html').name if idx < len(wszystkie) - 1 else None,
        })
        print(f'{cel.relative_to(REPO)} OK')


if __name__ == '__main__':
    main()
