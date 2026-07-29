#!/usr/bin/env python3
"""Przebuduj index.html — archiwum wydań gazety i raportów finansowych.

    python3 routine/buduj_index.py

Wołany AUTOMATYCZNIE przy publikacji (gazeta: KROK 5, raport: KROK 3) oraz przez
hook pre-commit — dzięki temu archiwum ZAWSZE linkuje świeżo dodane wydanie
(wpadka 24.07.2026: wydanie poranne poszło bez wpisu w index.html) i numer wersji
w stopce zgadza się z commitem publikującym.
"""
import datetime
import html as htmlmod
import pathlib
import re
import subprocess
import sys
from collections import OrderedDict

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import buduj_dane                                          # noqa: E402  (po ustawieniu ścieżki)

DNI = ['Poniedziałek', 'Wtorek', 'Środa', 'Czwartek', 'Piątek', 'Sobota', 'Niedziela']
MIESIACE = ['', 'stycznia', 'lutego', 'marca', 'kwietnia', 'maja', 'czerwca',
            'lipca', 'sierpnia', 'września', 'października', 'listopada', 'grudnia']

STYL = '''<style>
:root{--paper:#faf7f0;--ink:#17150f;--soft:#55503f;--rule:#d8d2c2;--accent:#8a1c1c;--card:#fff}
@media(prefers-color-scheme:dark){:root{--paper:#14130f;--ink:#ece7da;--soft:#a39d8b;--rule:#35322a;--accent:#e0655a;--card:#1d1b16}}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Inter,sans-serif;background:var(--paper);color:var(--ink);padding:48px 24px 80px;
  background-image:radial-gradient(ellipse 120% 60% at 50% -5%,color-mix(in srgb,#fff 45%,var(--paper)),var(--paper) 70%)}
body::before{content:"";position:fixed;inset:0;pointer-events:none;z-index:90;opacity:.045;mix-blend-mode:multiply;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='240' height='240'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2' stitchTiles='stitch'/%3E%3CfeColorMatrix type='saturate' values='0'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")}
@media(prefers-color-scheme:dark){body{background-image:none}body::before{opacity:.06;mix-blend-mode:screen}}
.wrap{max-width:720px;margin:0 auto}
header{text-align:center}
.kicker{font-size:.7em;text-transform:uppercase;letter-spacing:4px;color:var(--soft);
  display:flex;align-items:center;justify-content:center;gap:16px}
.kicker::before,.kicker::after{content:"";height:1px;width:clamp(30px,8vw,90px);background:var(--rule)}
h1{font-family:Fraunces,serif;font-weight:900;font-size:clamp(2.8em,8vw,4.5em);letter-spacing:-1px;line-height:1;margin:10px 0 4px}
h1 a{color:inherit;text-decoration:none}
.bar{border-top:1px solid var(--rule);border-bottom:3px double var(--ink);padding:10px 0;margin-top:20px;
  font-size:.72em;text-transform:uppercase;letter-spacing:2px;font-weight:600;color:var(--soft)}
.menu{display:flex;justify-content:center;gap:20px;flex-wrap:wrap;margin-top:14px;
  font-size:.74em;text-transform:uppercase;letter-spacing:1.5px;font-weight:700}
.menu a{color:var(--soft);text-decoration:none;border-bottom:1px solid var(--rule);padding-bottom:2px}
.menu a:hover{color:var(--accent);border-bottom-color:var(--accent)}
.day{margin-top:30px}
.day-head{font-family:Fraunces,serif;font-weight:700;font-size:1.05em;padding-bottom:8px;margin-bottom:10px;
  border-bottom:1px solid var(--rule)}
.day--reports{margin-bottom:44px}
.day--reports .day-head{color:var(--accent);border-bottom-color:var(--accent)}
.item{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:13px 16px;
  background:color-mix(in srgb,var(--card) 45%,var(--paper));border:1px solid var(--rule);border-radius:2px;
  margin-bottom:8px;text-decoration:none;color:var(--ink);transition:border-color .2s}
.item:hover{border-color:var(--accent)}
.item:hover .item-go{color:var(--accent)}
.item--latest{border-left:3px solid var(--accent)}
.item-label{font-weight:600;font-size:.88em;display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.item-go{font-size:.72em;color:var(--soft);text-transform:uppercase;letter-spacing:1.5px;font-weight:700;flex-shrink:0}
.badge{background:var(--accent);color:#fff;font-size:.65em;font-weight:700;text-transform:uppercase;
  letter-spacing:1px;padding:2px 7px;border-radius:2px}
footer{text-align:center;font-size:.7em;color:var(--soft);text-transform:uppercase;letter-spacing:1px;
  margin-top:60px;border-top:3px double var(--ink);padding-top:16px}
.wersja{display:block;margin-top:7px;font-size:.9em;letter-spacing:2px;opacity:.7}
.wersja a{color:inherit;text-decoration:none;border-bottom:1px solid var(--rule)}
.wersja a:hover{color:var(--accent);border-bottom-color:var(--accent)}
@media(max-width:600px){body{padding:32px 14px 60px}.item{padding:11px 12px}.item-go{display:none}}
</style>'''

SKRYPT = '''<script>
/* Godziny wydań zapisane są w UTC (data-iso); pokaż je w czasie polskim (Europe/Warsaw, z DST). */
document.querySelectorAll('time.ed-time[data-iso]').forEach(function (el) {
  var d = new Date(el.getAttribute('data-iso'));
  if (isNaN(d.getTime())) return;
  try {
    el.textContent = new Intl.DateTimeFormat('pl-PL', {
      timeZone: 'Europe/Warsaw', hour: '2-digit', minute: '2-digit', hour12: false
    }).format(d);
  } catch (e) {}
});
</script>'''


def git(*args, timeout=120) -> str:
    return subprocess.run(['git', *args], cwd=REPO, capture_output=True, text=True,
                          check=True, timeout=timeout).stdout.strip()


def numer_wersji() -> str:
    """`vN` w stopce = numer commita, który ten build opublikuje.

    Rutyny przebudowują archiwum tuż przed swoim jedynym commitem, więc „+1"
    celuje dokładnie w commit publikujący. Brak osobnego pliku z wersją oznacza,
    że równoległe pushe rutyn nie mają o co się pobić.

    Klon w środowisku rutyny bywa PŁYTKI — wtedy `rev-list --count` liczy tylko
    pobrany fragment historii i numer kłamie (audyt 29.07.2026: rutyna wpisała
    v52, gdy repo miało 91 commitów). Dlatego najpierw dociągamy pełną historię;
    to kilka MB, bo repo trzyma grafiki wydań poza gitem."""
    try:
        if git('rev-parse', '--is-shallow-repository') == 'true':
            try:
                git('fetch', '--unshallow', '--quiet')
            except Exception:
                pass                                      # bez sieci zostaje niepełny licznik
        wersja = f'v{int(git("rev-list", "--count", "HEAD")) + 1}'
    except Exception:
        return ''
    return (f'<span class="wersja"><a href="https://github.com/kapitanski-dev/kapitanski-dev.github.io'
            f'/commits/main" title="Zbudowano {datetime.date.today().isoformat()}" rel="noopener">'
            f'{wersja}</a></span>')


def wydania() -> str:
    """Karty wydań gazety, pogrupowane po dniach (najnowszy dzień pierwszy)."""
    pliki = sorted((REPO / 'wydania').glob('*.html'), reverse=True)
    lista = []
    for f in pliki:
        m = re.match(r'(\d{4}-\d{2}-\d{2})-(rano|wieczor)(?:-(\d{4}))?$', f.stem)
        if not m:
            continue
        data_str, typ, gg = m.group(1), m.group(2), m.group(3)
        try:
            d = datetime.date.fromisoformat(data_str)
        except ValueError:
            continue
        lista.append({
            'url': f'wydania/{f.name}',
            'label': 'Wydanie poranne' if typ == 'rano' else 'Wydanie wieczorne',
            'icon': '☀️' if typ == 'rano' else '🌙',
            # Godzina z nazwy pliku jest w UTC; przeglądarka przeliczy ją na czas PL.
            'time': f'{gg[:2]}:{gg[2:]}' if gg else '',
            'iso': f'{data_str}T{gg[:2]}:{gg[2:]}:00Z' if gg else '',
            'date': f"{DNI[d.weekday()]}, {d.day} {MIESIACE[d.month]} {d.year}",
            'first': False,
        })
    if lista:
        lista[0]['first'] = True

    dni = OrderedDict()
    for e in lista:
        dni.setdefault(e['date'], []).append(e)
    print(f'index.html OK — {len(lista)} wydań')
    return ''.join(
        f'<div class="day"><div class="day-head">{data}</div>' + ''.join(
            f'<a href="{e["url"]}" class="item{" item--latest" if e["first"] else ""}">'
            + f'<span class="item-label">{e["icon"]} {e["label"]}'
            + (f' &middot; <time class="ed-time" data-iso="{e["iso"]}">{e["time"]}</time>' if e["time"] else '')
            + ("<span class=badge>Najnowsze</span>" if e["first"] else "") + '</span>'
            + '<span class="item-go">Czytaj &rarr;</span></a>' for e in pozycje) + '</div>\n'
        for data, pozycje in dni.items()
    )


def raporty() -> str:
    """Sekcja raportów finansowych. Linkujemy tylko te ze zbudowanym `.html` — sam
    `.md` dałby w archiwum 404."""
    lista = []
    for f in sorted((REPO / 'raport-finansowy').glob('*.md'), reverse=True):
        if not f.with_suffix('.html').exists():
            continue
        fm = f.read_text(encoding='utf-8')[:800]
        m_data = re.search(r'^date:\s*(\d{4}-\d{2}-\d{2})', fm, re.M)
        data_str = m_data.group(1) if m_data else f.stem[:10]
        try:
            d = datetime.date.fromisoformat(data_str)
        except ValueError:
            continue
        m_tytul = re.search(r'^title:\s*["\']?(.+?)["\']?\s*$', fm, re.M)
        tytul = (m_tytul.group(1).strip() if m_tytul
                 else f'Przegląd rynku — {d.day} {MIESIACE[d.month]} {d.year}')
        lista.append({'url': f'raport-finansowy/{f.stem}.html', 'title': tytul, 'sort': (d, f.stem)})

    if not lista:
        return ''
    lista.sort(key=lambda r: r['sort'], reverse=True)
    return '<div class="day day--reports"><div class="day-head">Raporty finansowe</div>' + ''.join(
        f'<a href="{r["url"]}" class="item{" item--latest" if i == 0 else ""}">'
        + f'<span class="item-label">📈 {htmlmod.escape(r["title"])}</span>'
        + '<span class="item-go">Czytaj &rarr;</span></a>' for i, r in enumerate(lista)
    ) + '</div>\n'


def main() -> None:
    (REPO / 'wydania').mkdir(exist_ok=True)
    # Strony pochodne (szukaj / kalendarz / angielski) jadą z tych samych wydań co
    # archiwum, więc budujemy je tym samym poleceniem — nie ma jak o nich zapomnieć.
    buduj_dane.main()
    strona = '''<!DOCTYPE html>
<html lang="pl"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Grzyb Times — archiwum</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,700;9..144,900&family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
''' + STYL + '''</head>
<body><div class="wrap">
<header><div class="kicker">Archiwum wydań</div><h1><a href="/">Grzyb Times</a></h1>
<div class="bar">Redagowane przez AI &middot; wydania poranne i wieczorne &middot; raporty finansowe</div>
<nav class="menu"><a href="/szukaj.html">Szukaj w archiwum</a><a href="/kalendarz.html">Kalendarium</a><a href="/angielski.html">Angielski</a></nav></header>
''' + raporty() + wydania() + '''<footer>Grzyb Times &mdash; redagowane przez AI''' + numer_wersji() + '''</footer></div>
''' + SKRYPT + '''
</body></html>'''
    (REPO / 'index.html').write_text(strona, encoding='utf-8')


if __name__ == '__main__':
    main()
