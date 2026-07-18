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
tytuł gazety, lista kategorii (kolejność = ważność, pierwsza = hero), **`liczba`
artykułów dla każdej kategorii**, `zrodla_pierwotne`, reguły research wtórny.
**Nie zgaduj — użyj wartości z pliku.** Łączna liczba artykułów wydania = suma
pól `liczba` ze wszystkich kategorii.

## KROK 1 — Research

Użyj WebSearch. Dla **każdej** kategorii z `config.yaml` (w kolejności) znajdź
**dokładnie tyle artykułów, ile wynosi jej pole `liczba`** — najważniejsze
wiadomości z ostatnich 12 h z domen z `zrodla_pierwotne`. W obrębie kategorii
uporządkuj je od najważniejszego do najmniej istotnego. Jeśli w źródłach nie ma
tylu sensownych materiałów dla kategorii — dodaj tyle, ile realnie jest (nie
duplikuj tematów i nie wychodź poza listę źródeł).

Kolejność w wynikowej liście `artykuly`: kategorie w kolejności z configu, a w
obrębie każdej kategorii artykuły od najważniejszego. Pierwszy artykuł na liście
(kategoria **Okładka**) = wielki artykuł okładkowy otwierający wydanie.

**Okładka** (pierwsza kategoria, `liczba: 1`): wybierz JEDNĄ, absolutnie
najważniejszą wiadomość dnia — z dowolnego tematu (rynki, polityka, wojna,
technologia, nauka). To ma być „news numer jeden". **Nie powielaj** tej samej
wiadomości w żadnej innej kategorii — jeśli najważniejszy news jest np.
polityczny, w kategorii Polityka daj inne tematy.

**Obrazy — NIE pobieraj ich z artykułu** (zdjęcia Reuters/Bloomberg są chronione
przed hotlinkingiem i nie załadują się na GitHub Pages). Zamiast tego dla każdego
artykułu podaj pole `obraz.query`: **precyzyjną, ANGIELSKĄ frazę** (2–5 słów)
wskazującą konkretny, fotografowalny obiekt związany z tematem. Skrypt w KROK 3
zamieni ją na realne zdjęcie z Wikimedia Commons, a fraza `query` zostaje zapisana
w wydaniu — jeśli API zawiedzie w chmurze, obraz rozwiąże sama przeglądarka
czytelnika (IP domowe, bez limitów). **Zawsze podawaj sensowną, konkretną `query`.**

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
- **Kwoty — ZAWSZE waluta + PLN w nawiasie:** każdą kwotę pieniężną w **tytule** i w
  **akapitach** podawaj w walucie oryginalnej, a bezpośrednio po niej dopisz w nawiasie
  przybliżoną wartość w złotych po **aktualnym kursie**, poprzedzoną tyldą — np.
  „Apple wyceniono na 4,9 bln USD (~19,6 bln zł)”, „ropa Brent 85,92 USD (~312 zł)”.
  - **Kurs pobierz w researchu** (WebSearch, kurs bieżący z dnia wydania) i użyj go
    spójnie w całym wydaniu. Zaokrąglaj rozsądnie (2–3 cyfry znaczące).
  - Wyjątek: kwota podana już w **PLN** — nie przeliczaj i nie dodawaj nawiasu.
  - Ta sama zasada obowiązuje w `kluczowe_liczby`, jeśli wartość jest kwotą (np.
    `"wartosc": "4,9 bln USD (~19,6 bln zł)"`).
- **kluczowe_liczby:** 1–3 najważniejsze wartości liczbowe artykułu.
- **wykres:** tylko gdy masz zweryfikowane realne dane; `typ` = `"linia"` lub
  `"slupki"`; przy kategorii z `wykres: nie` — pomiń. Nie wymyślaj danych.
  - Dąż do **szczegółowości**: podawaj **8–15 punktów** danych (np. notowania z
    kolejnych dni/godzin), nie 3–4. Etykiety (`etykiety`) dla każdego punktu.
  - Dodaj `jednostka` (np. `"%"`, `" pkt"`, `" USD"`, `" mld"`) — pokaże się w
    interaktywnym tooltipie i na osi Y. Wykres jest interaktywny (najechanie
    pokazuje wartość punktu), więc realne, gęste dane mają największą wartość.

## KROK 2.5 — Zbieraj logi (sekcja „Logs” w gazecie)

Przez **całe** wykonanie (KROK 1–3) notuj zdarzenia, które pomogą nam potem
ulepszać gazetę, i dodawaj je do listy `dane["logi"]` jako obiekty
`{"poziom": ..., "wiadomosc": ...}` (poziom: `"error"`, `"warning"` lub `"info"`).
W skrypcie z KROK 3 służy do tego funkcja `log(poziom, wiadomosc)`.

**Co logować (przykłady):**
- **Błędy narzędzi** — dosłowną treść, np. z WebSearch/WebFetch:
  `log("error", "API Error: 400 The following domains are not accessible to our user agent: ['reuters.com']. Read more: https://support.anthropic.com/...")`.
- **Źródło niedostępne / zablokowane** dla bota, przekierowania, paywall, timeouty.
- **Braki w kategoriach** — za mało sensownych materiałów, by wypełnić `liczba`
  (np. `log("warning", "Kategoria „Wojna”: znaleziono 2 z 3 wymaganych artykułów.")`).
- **Problemy z danymi** — brak wiarygodnych liczb do wykresu, rozbieżne wartości
  między źródłami, brak aktualnego kursu walutowego do przeliczenia na PLN.
- **Obrazy** — brak sensownego obiektu na `obraz.query`, nieudana resolucja.
- **Info** — istotne decyzje redakcyjne, obejścia, nietypowe sytuacje warte uwagi.

Zasady: notuj **konkretnie** (kategoria, artykuł, dosłowny komunikat błędu, URL
pomocy jeśli był). Nie loguj rzeczy oczywistych ani szumu. Jeśli wszystko poszło
gładko — zostaw `logi` puste (gazeta pokaże „Brak zdarzeń”). Część logów skrypt
z KROK 3 dopisze automatycznie (nierozwiązane obrazy, rozbieżność liczby artykułów).

## KROK 3 — Wygeneruj plik wydania

W poniższym skrypcie **ustaw `WYDANIE`** na wartość z promptu (`rano` albo `wieczor`),
zbuduj listę `artykuly` (w kolejności kategorii z configu), **dopisz `log(...)`
dla problemów z KROK 1–2** (patrz KROK 2.5) i uruchom:

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
  "data_wydania": f"{days_pl[today.weekday()]}, {today.day} {months_pl[today.month]} {today.year}, {now.strftime('%H:%M')}",
  "numer": etykieta,
  "artykuly": [],  # <-- wstaw artykuły (patrz schemat niżej); każdy z obraz.query (fraza EN)
  "logi": []       # <-- zdarzenia z uruchomienia rutyny -> sekcja „Logs” w gazecie (patrz KROK 2.5)
}

def log(poziom, wiadomosc):
    """Dodaj wpis do sekcji „Logs”. poziom: 'error' | 'warning' | 'info'."""
    dane["logi"].append({"poziom": poziom, "wiadomosc": wiadomosc})
    print(f"  LOG[{poziom}] {wiadomosc}")

# >>> Wklej tu wpisy log(...) dla problemów napotkanych w KROK 1–2 (patrz KROK 2.5),
#     np. log("error", "API Error: 400 ... domains not accessible ... ['reuters.com'] ...")

# --- Rezolwer obrazów: fraza EN -> realny, hotlinkowalny URL z Wikimedia Commons ---
import urllib.request, urllib.parse

# Wikimedia wymaga opisowego User-Agenta z kontaktem; generyczne UA + IP datacenter
# bywają blokowane (403/429) — to powodowało puste obrazy w poprzednich wydaniach.
# Stąd: opisowy UA + kilka prób z odczekaniem. A gdyby i tak się nie udało — przeglądarka
# rozwiąże brakujące obrazy klient-side z zachowanej frazy `query` (patrz template.html).
import time
WIKI_UA = 'GrzybTimes/1.0 (https://kapitanski-dev.github.io; tomasz.grzybowski94@gmail.com)'

def wikimedia_image(query):
    if not query: return ""
    params = {'action':'query','generator':'search','gsrsearch':query,'gsrnamespace':'6',
              'gsrlimit':'8','prop':'imageinfo','iiprop':'url|mime','iiurlwidth':'1000','format':'json'}
    url = 'https://commons.wikimedia.org/w/api.php?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={'User-Agent': WIKI_UA})
    data = None
    for attempt in range(3):                       # retry na wypadek 429/timeout
        try:
            data = json.load(urllib.request.urlopen(req, timeout=25)); break
        except Exception:
            time.sleep(1.5 * (attempt + 1))
    if data is None:
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
    # WAŻNE: zachowaj `query` w JSON — dzięki temu przeglądarka rozwiąże obraz nawet,
    # gdy `url` tu wyjdzie pusty (blokada API w chmurze). q == "" (celowo) -> placeholder.
    a["obraz"] = {"url": wikimedia_image(q), "query": q, "alt": obraz.get("alt") or a["tytul"]}
    time.sleep(0.4)          # łagodne tempo — nie wywołuj rate-limitu Wikimedia
    print(f"  [{a['kategoria']}] {q!r} -> {a['obraz']['url'] or '(pusty — rozwiąże przeglądarka z query)'}")
    if q and not a["obraz"]["url"]:   # obraz nierozwiązany przy generowaniu -> log (przeglądarka spróbuje ponownie)
        log("warning", f"Obraz nierozwiązany przy generowaniu: [{a['kategoria']}] „{a['tytul']}” (query: {q!r}). Rozwiąże go przeglądarka czytelnika.")

# --- Kontrola: liczba artykułów na kategorię wg config.yaml (rozbieżności -> log) ---
from collections import Counter
oczek = {k['nazwa']: k.get('liczba', 1) for k in cfg['kategorie']}
masz = Counter(a['kategoria'] for a in dane['artykuly'])
for kat, n in oczek.items():
    if masz.get(kat, 0) != n:
        print(f"  ⚠ {kat}: jest {masz.get(kat,0)}, config oczekuje {n}")
        log("warning", f"Kategoria „{kat}”: złożono {masz.get(kat,0)} art., config oczekuje {n}.")
print(f"Artykułów łącznie: {len(dane['artykuly'])} (config: {sum(oczek.values())})")
print(f"Logów: {len(dane['logi'])}")

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
  "wykres": {"typ": "linia", "tytul": "S&P 500 — 10 sesji", "jednostka": " pkt",
             "etykiety": ["1.07","2.07","3.07","4.07","7.07","8.07","9.07","10.07","11.07","14.07"],
             "wartosci": [6320,6345,6338,6360,6402,6390,6455,6480,6472,6512]},
  "akapity": ["Akapit 1 — fakty.", "Akapit 2 — konsekwencje."]
}
```

Schemat wpisu logu (`dane["logi"]` — dodawany funkcją `log(poziom, wiadomosc)`):

```json
{"poziom": "error", "wiadomosc": "API Error: 400 The following domains are not accessible to our user agent: ['reuters.com']. Read more: https://support.anthropic.com/..."}
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
