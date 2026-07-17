# Instrukcja generowania wydania „Grzyb Times”

Jesteś profesjonalnym edytorem i researcherem. Wygeneruj jedno wydanie gazety
**Grzyb Times** i opublikuj je na GitHub Pages (`kapitanski-dev/kapitanski-dev.github.io`).

Parametr **`WYDANIE`** (`rano` albo `wieczor`) pochodzi z promptu routine, który
Cię uruchomił. Trzymaj się tej instrukcji dokładnie — cała konfiguracja, szablon
i logika są w repo.

Mapowanie `WYDANIE`:

| WYDANIE | kicker / numer | ikona w archiwum | godziny |
|---|---|---|---|
| `rano`    | „Wydanie poranne”   | ☀️ | poranne notowania/newsy |
| `wieczor` | „Wydanie wieczorne” | 🌙 | popołudniowe/wieczorne podsumowanie |

## KROK 0 — Repo i konfiguracja

Repozytorium jest już sklonowane w środowisku. Zlokalizuj je i wczytaj config:

```bash
REPO=$(find /home /root /workspace /tmp -maxdepth 6 -name ".git" 2>/dev/null | grep -v '/.git/' | head -1 | xargs dirname 2>/dev/null)
echo "Repo: $REPO" && ls "$REPO"
```

Przeczytaj `"$REPO/config.yaml"` (narzędzie Read). Stamtąd pochodzą:
tytuł gazety, lista kategorii (kolejność = ważność, pierwsza = hero),
`liczba_artykulow`, `zrodla_pierwotne`, reguły research wtórny.
**Nie zgaduj — użyj wartości z pliku.**

## KROK 1 — Research

Użyj WebSearch. Dla **każdej** kategorii z `config.yaml` (w kolejności) znajdź
najważniejszą wiadomość z ostatnich 12 h pochodzącą z domeny z `zrodla_pierwotne`.
Jeśli w żadnym źródle nie ma nic sensownego dla kategorii — wybierz najlepszy
dostępny materiał z listy, nie wychodząc poza nią.

**Obrazy — NIE pobieraj ich z artykułu** (zdjęcia Reuters/Bloomberg są chronione
przed hotlinkingiem i nie załadują się na GitHub Pages). Zamiast tego dla każdego
artykułu podaj pole `obraz.query`: **precyzyjną, ANGIELSKĄ frazę** (2–5 słów)
wskazującą konkretny, fotografowalny obiekt związany z tematem. Skrypt w KROK 3
sam zamieni ją na realne zdjęcie z Wikimedia Commons.

Dobre `obraz.query` = konkretny obiekt, nie abstrakcja:
- osoba: `Jerome Powell`, `Donald Tusk`, `Sam Altman`
- miejsce/budynek: `Warsaw Stock Exchange`, `Federal Reserve building`, `Strait of Hormuz`
- rzecz/logo: `Leopard 2 tank`, `NVIDIA logo`, `James Webb Space Telescope`
❌ unikaj abstraktów (`inflation`, `economy growth`) — dają losowe wykresy.
Jeśli naprawdę nie ma sensownego obiektu, ustaw `obraz.query` = `""`.

Research wtórny (poza listą) tylko jeśli `research_wtorny.dozwolony: true` i
wyłącznie do weryfikacji liczb, kontekstu lub danych do wykresu. Źródło wtórne
nigdy nie jest linkiem artykułu (`zrodlo.url`).

## KROK 2 — Redakcja

- **Tytuł:** rzeczowy, bez emocji (❌ „Gigantyczny krach!” → ✅ „S&P 500 spadł o 2,3%”).
- **Dokładnie 2 akapity:** (1) fakty i liczby; (2) dlaczego to ważne / konsekwencje.
- **Ton:** obiektywny, agencyjny, zero marketingu.
- **kluczowe_liczby:** 1–3 najważniejsze wartości liczbowe artykułu.
- **wykres:** tylko gdy masz zweryfikowane realne dane; `typ` = `"linia"` lub
  `"slupki"`; przy kategorii z `wykres: nie` — pomiń. Nie wymyślaj danych.

## KROK 3 — Wygeneruj plik wydania

W poniższym skrypcie **ustaw `WYDANIE`** na wartość z promptu (`rano` albo `wieczor`),
zbuduj listę `artykuly` (w kolejności kategorii z configu) i uruchom:

```python
import json, pathlib, subprocess, datetime
try:
    import yaml
except ImportError:
    subprocess.run("pip install pyyaml -q", shell=True)
    import yaml

WYDANIE = "rano"   # <-- ustaw: "rano" albo "wieczor"

REPO = subprocess.run(
    "find /home /root /workspace /tmp -maxdepth 6 -name '.git' 2>/dev/null | grep -v '/.git/' | head -1 | xargs dirname 2>/dev/null",
    shell=True, capture_output=True, text=True).stdout.strip()
repo = pathlib.Path(REPO)

cfg = yaml.safe_load((repo / 'config.yaml').read_text())
tytul = cfg['wydanie']['tytul']
tpl = (repo / 'template.html').read_text()

etykieta = 'Wydanie poranne' if WYDANIE == 'rano' else 'Wydanie wieczorne'
now = datetime.datetime.now()
today = now.date()
days_pl = ['poniedziałek','wtorek','środa','czwartek','piątek','sobota','niedziela']
months_pl = ['','stycznia','lutego','marca','kwietnia','maja','czerwca','lipca','sierpnia','września','października','listopada','grudnia']

dane = {
  "tytul": tytul,
  "kicker": f"{etykieta} · Redagowane przez AI",
  "data_wydania": f"{days_pl[today.weekday()]}, {today.day} {months_pl[today.month]} {today.year}",
  "numer": etykieta,
  "artykuly": []   # <-- wstaw artykuły (patrz schemat niżej); każdy z obraz.query (fraza EN)
}

# --- Rezolwer obrazów: fraza EN -> realny, hotlinkowalny URL z Wikimedia Commons ---
import urllib.request, urllib.parse

def wikimedia_image(query):
    if not query: return ""
    params = {'action':'query','generator':'search','gsrsearch':query,'gsrnamespace':'6',
              'gsrlimit':'8','prop':'imageinfo','iiprop':'url|mime','iiurlwidth':'1000','format':'json'}
    url = 'https://commons.wikimedia.org/w/api.php?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={'User-Agent':'GrzybTimes/1.0 (news bot)'})
    try:
        data = json.load(urllib.request.urlopen(req, timeout=20))
    except Exception:
        return ""
    pages = (data.get('query') or {}).get('pages') or {}
    for p in sorted(pages.values(), key=lambda p: p.get('index', 999)):
        ii = (p.get('imageinfo') or [{}])[0]
        if ii.get('mime') in ('image/jpeg','image/png','image/webp'):
            return ii.get('thumburl') or ii.get('url','')
    return ""

for a in dane["artykuly"]:
    obraz = a.get("obraz") or {}
    q = obraz.get("query")
    if q is None:            # brak pola query -> użyj tytułu artykułu
        q = a["tytul"]
    # q == "" (agent celowo pusty) -> URL pusty -> czysty placeholder SVG
    a["obraz"] = {"url": wikimedia_image(q), "alt": obraz.get("alt") or a["tytul"]}
    print(f"  [{a['kategoria']}] {q!r} -> {a['obraz']['url'] or '(brak — placeholder SVG)'}")

out = tpl.replace('__DANE__', json.dumps(dane, ensure_ascii=False, indent=2))
assert '__DANE__' not in out
filename = f"{today}-{WYDANIE}-{now.strftime('%H%M')}.html"
pathlib.Path('/tmp/grzyb_times.html').write_text(out, encoding='utf-8')
print(f'OK — {len(out):,} bajtów | plik: {filename}')
```

Schemat artykułu (podajesz `obraz.query` — angielską frazę; skrypt sam doda `obraz.url`):

```json
{
  "kategoria": "Inwestowanie",
  "tytul": "Rzeczowy tytuł z liczbą",
  "zrodlo": {"nazwa": "Reuters", "url": "https://...", "godzina": "07:30"},
  "obraz": {"query": "Warsaw Stock Exchange", "alt": "opis zdjęcia po polsku"},
  "kluczowe_liczby": [{"wartosc": "2,3%", "opis": "spadek indeksu"}],
  "wykres": {"typ": "linia", "tytul": "...", "etykiety": ["..."], "wartosci": [0]},
  "akapity": ["Akapit 1 — fakty.", "Akapit 2 — konsekwencje."]
}
```

Weryfikacja poprawności JSON w pliku:

```bash
python3 -c "import json,pathlib; h=pathlib.Path('/tmp/grzyb_times.html').read_text(); s=h[h.index('application/json')+18:]; s=s[:s.index('</script>')].strip(); json.loads(s); print('JSON OK')"
```

## KROK 4 — Zaktualizuj index.html (archiwum)

```python
import pathlib, datetime, subprocess, re

REPO = subprocess.run(
    "find /home /root /workspace /tmp -maxdepth 6 -name '.git' 2>/dev/null | grep -v '/.git/' | head -1 | xargs dirname 2>/dev/null",
    shell=True, capture_output=True, text=True).stdout.strip()
repo = pathlib.Path(REPO)
(repo / 'wydania').mkdir(exist_ok=True)
files = sorted((repo / 'wydania').glob('*.html'), reverse=True)

days_pl = ['Poniedziałek','Wtorek','Środa','Czwartek','Piątek','Sobota','Niedziela']
months_pl = ['','stycznia','lutego','marca','kwietnia','maja','czerwca','lipca','sierpnia','września','października','listopada','grudnia']

editions = []
for f in files:
    m = re.match(r'(\d{4}-\d{2}-\d{2})-(rano|wieczor)(?:-(\d{4}))?$', f.stem)
    if not m: continue
    date_str, etype, tc = m.group(1), m.group(2), m.group(3)
    try: d = datetime.date.fromisoformat(date_str)
    except: continue
    label = 'Wydanie poranne' if etype == 'rano' else 'Wydanie wieczorne'
    icon = '☀️' if etype == 'rano' else '🌙'
    time_str = f' · {tc[:2]}:{tc[2:]}' if tc else ''
    date_fmt = f"{days_pl[d.weekday()]}, {d.day} {months_pl[d.month]} {d.year}"
    editions.append({'url': f'wydania/{f.name}', 'label': label + time_str, 'icon': icon, 'date': date_fmt, 'first': False})

if editions: editions[0]['first'] = True
cards = ''.join(
    f'<a href="{e["url"]}" class="item{" item--latest" if e["first"] else ""}">'
    + f'<span class="item-label">{e["icon"]} {e["label"]}{"<span class=badge>Najnowsze</span>" if e["first"] else ""}</span>'
    + f'<span class="item-date">{e["date"]}</span></a>\n' for e in editions
)
html = '''<!DOCTYPE html>
<html lang="pl"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Grzyb Times</title>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,900&family=Inter:wght@400;600&display=swap" rel="stylesheet">
<style>:root{--paper:#faf7f0;--ink:#17150f;--soft:#55503f;--rule:#d8d2c2;--accent:#8a1c1c}*{box-sizing:border-box;margin:0;padding:0}body{font-family:Inter,sans-serif;background:var(--paper);color:var(--ink);padding:48px 24px 80px}.wrap{max-width:720px;margin:0 auto}h1{font-family:Fraunces,serif;font-weight:900;font-size:clamp(2.8em,8vw,4.5em);letter-spacing:-2px;line-height:1;margin-bottom:6px}.sub{font-size:.7em;text-transform:uppercase;letter-spacing:4px;color:var(--soft)}hr{border:none;border-top:3px double var(--ink);margin:32px 0 24px}.section{font-size:.68em;font-weight:700;text-transform:uppercase;letter-spacing:3px;color:var(--soft);margin-bottom:14px}.item{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:16px 18px;background:#fff;border:1px solid var(--rule);border-radius:8px;margin-bottom:8px;text-decoration:none;color:var(--ink);transition:border-color .2s,transform .15s}.item:hover{border-color:var(--accent);transform:translateX(3px)}.item--latest{border:2px solid var(--accent)}.item-label{font-weight:600;font-size:.88em;display:flex;align-items:center;gap:10px}.item-date{font-size:.8em;color:var(--soft);flex-shrink:0}.badge{background:var(--accent);color:#fff;font-size:.65em;font-weight:700;text-transform:uppercase;letter-spacing:1px;padding:2px 7px;border-radius:3px}footer{text-align:center;font-size:.7em;color:var(--soft);text-transform:uppercase;letter-spacing:1px;margin-top:60px}@media(max-width:600px){body{padding:32px 16px 60px}.item{flex-direction:column;align-items:flex-start;gap:4px}}</style></head>
<body><div class="wrap"><h1>Grzyb Times</h1><p class="sub">Archiwum wydań</p><hr><div class="section">Wszystkie wydania</div>
''' + cards + '''<footer>Grzyb Times &mdash; redagowane przez AI</footer></div></body></html>'''
(repo / 'index.html').write_text(html, encoding='utf-8')
print(f'index.html OK — {len(editions)} wydań')
```

## KROK 5 — Commit & push

```bash
DATE=$(python3 -c "import datetime; print(datetime.date.today())")
TIME=$(python3 -c "import datetime; print(datetime.datetime.now().strftime('%H%M'))")
cd "$REPO"
git config user.email "grzyb-times@auto.bot"
git config user.name "Grzyb Times Bot"
mkdir -p wydania
cp /tmp/grzyb_times.html wydania/${DATE}-${WYDANIE}-${TIME}.html
git add wydania/${DATE}-${WYDANIE}-${TIME}.html index.html
git commit -m "Grzyb Times — ${WYDANIE} ${DATE} ${TIME}"
git push origin main
echo "Opublikowano: https://kapitanski-dev.github.io/wydania/${DATE}-${WYDANIE}-${TIME}.html"
```

Na koniec podaj użytkownikowi link do opublikowanego wydania i jedno zdanie o
najważniejszej wiadomości dnia.
