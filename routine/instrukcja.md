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
artykułów dla każdej kategorii**, **`wydanie.akapity`** (liczba akapitów na
artykuł, domyślnie 3), `zrodla_pierwotne`, reguły research wtórny.
**Nie zgaduj — użyj wartości z pliku.** Łączna liczba artykułów wydania = suma
pól `liczba` ze wszystkich kategorii.

## KROK 0.5 — Uwagi czytelników (GitHub Issues)

Czytelnicy zgłaszają uwagi przyciskiem „Zgłoś uwagę” przy artykule (tworzy issue
z tytułem `[Uwaga] …`). Pobierz otwarte zgłoszenia (jedno tanie wywołanie,
publiczne API bez tokena):

```bash
curl -s "https://api.github.com/repos/kapitanski-dev/kapitanski-dev.github.io/issues?state=open&per_page=20" \
 | python3 -c "import json,sys; [print('-', i['title'], '::', (i.get('body') or '')[:300].replace(chr(10),' ')) for i in json.load(sys.stdin) if i['title'].startswith('[Uwaga]')]"
```

- **Uwzględnij zasadne uwagi** w bieżącym wydaniu (wskazany błąd merytoryczny,
  prośba o temat/doprecyzowanie). Każdą uwzględnioną zaloguj:
  `log("info", "Uwaga czytelnika uwzględniona: <tytuł issue> — <co zrobiono>")`.
- Uwagę bezzasadną lub nie na teraz po prostu pomiń (bez logowania).
- **Nie odpowiadaj na issue i nie zamykaj ich** — to robi użytkownik.
- Brak zgłoszeń = idź dalej, nic nie loguj.

## KROK 1 — Research

Użyj WebSearch. Dla **każdej** kategorii z `config.yaml` (w kolejności) znajdź
**dokładnie tyle artykułów, ile wynosi jej pole `liczba`** — wiadomości
z ostatnich 12 h z domen z `zrodla_pierwotne`. Jeśli w źródłach nie ma tylu
sensownych materiałów dla kategorii — dodaj tyle, ile realnie jest (nie
duplikuj tematów i nie wychodź poza listę źródeł).

- **Weekend/święta (Inwestowanie):** gdy giełdy są zamknięte, okno dla
  Inwestowania rozszerza się do 48 h (podsumowania tygodnia, zapowiedzi).
  Nie sięgaj po newsy starsze niż 48 h — lepiej mniej artykułów.
- **`zrodlo.url` = KONKRETNY artykuł, nie strona główna.** Jeśli wyniki
  wyszukiwania nie dają bezpośredniego URL-a, wybierz inny temat/źródło,
  które go ma. Link do strony głównej lub kategorii serwisu — tylko w
  ostateczności i z wpisem `log("warning", ...)`.

**Jak wybierać, gdy kandydatów jest więcej niż `liczba` (RUBRYKA OCENY).**
Oceń każdego kandydata w myślach (nie wypisuj punktacji — szkoda tokenów)
według trzech kryteriów, w tej kolejności wag:
1. **Realny skutek (waga 3)** — jak duży i trwały wpływ na ludzi, gospodarkę,
   rynki. Fakty i podjęte decyzje > zapowiedzi, spekulacje i komentarze.
2. **Skala i zasięg (waga 2)** — ilu ludzi / jak duży kapitał / ile krajów
   dotyczy. Globalne > lokalne (chyba że temat wprost dotyczy Polski).
3. **Nowość i przełomowość (waga 1)** — rzeczy bez precedensu lub zmieniające
   trend > kolejny odcinek znanej historii.
Wybierz top `liczba` wg łącznej oceny i uporządkuj malejąco. Rozstrzyganie
remisów: wyżej to, co bardziej konkretne (zweryfikowane liczby, podjęte
decyzje) — niżej „może / planuje / rozważa”.

**Paywall — link artykułu ma być czytelny.** Czytelnik klika `zrodlo.url`, żeby
doczytać — link za twardym paywallem (np. **bloomberg.com**) jest dla niego
bezwartościowy. Gdy temat jest dostępny w kilku źródłach z listy, na `zrodlo.url`
wybierz link czytelny bez paywalla, a źródło paywallowane dopisz w
`zrodla_dodatkowe`. Jeśli temat jest TYLKO w źródle paywallowanym — użyj go
(lepszy paywall niż brak tematu).

**Oszczędzaj tokeny — research ma być zwięzły:**
- Celuj w **1 WebSearch na kategorię** (ewentualnie 1 dodatkowe, gdy pierwsze nie
  wystarczyło). Nie przeszukuj w kółko tego samego.
- **`WebFetch` tylko wtedy, gdy naprawdę musisz** odczytać konkretne liczby/cytat,
  których nie ma w wynikach wyszukiwania. Nie pobieraj całych stron „na zapas”.
- **Nie odpytuj domen, które blokują bota** (błąd 400 „domain not accessible”, np.
  reuters.com). Jeśli trafisz na taką — zaloguj (KROK 2.5) i pomiń, nie ponawiaj.
- **Research wtórny — tylko WYJĄTKOWO** (reguła niżej). Wykres buduj z danych,
  które już masz ze źródła pierwotnego — jeśli wymagałby osobnego researchu, pomiń go.

Kolejność w wynikowej liście `artykuly`: kategorie w kolejności z configu, a w
obrębie każdej kategorii artykuły od najważniejszego. Pierwszy artykuł na liście
(kategoria **Okładka**) = wielki artykuł okładkowy otwierający wydanie.

**Okładka** (pierwsza kategoria, `liczba: 1`): wybierz JEDNĄ, absolutnie
najważniejszą wiadomość dnia — z dowolnego tematu (rynki, polityka, wojna,
technologia, nauka). To ma być „news numer jeden". **Nie powielaj** tej samej
wiadomości w żadnej innej kategorii — jeśli najważniejszy news jest np.
polityczny, w kategorii Polityka daj inne tematy.

**Deduplikacja względem poprzedniego wydania (OBOWIĄZKOWA).** Zanim zaczniesz
research, przeczytaj NAJNOWSZY plik z `"$REPO/wydania/"` (sortowanie po nazwie,
ostatni = poprzednie wydanie) i wynotuj jego tematy (tytuły + kategorie z JSON-a
w `<script id="dane-gazety">`). To czytanie lokalne — nie kosztuje tokenów sieci.
Reguły:
- **Nie powtarzaj newsa z poprzedniego wydania**, jeśli nie wydarzyło się nic
  nowego — wybierz inny temat.
- **Temat wolno kontynuować tylko z wartością dodaną**: nowe fakty, liczby,
  reakcje, skutki, dalszy rozwój. Artykuł-kontynuacja musi zaczynać się od tego,
  co NOWE (nie streszczaj od zera), a w drugim akapicie krótko nawiązać do
  poprzedniego stanu („po wczorajszym…”).
- W artykule-kontynuacji ustaw pole **`"kontynuacja": true`** — gazeta pokaże
  badge „Aktualizacja”.
- Jeśli musiałeś odrzucić temat przez duplikację — to normalne, nie loguj tego;
  zaloguj tylko, gdy przez deduplikację nie dało się wypełnić `liczba` kategorii.

**Obrazy — NIE zajmujesz się nimi w rutynie.** Każdy artykuł dostanie automatycznie
zdjęcie **swojej kategorii** (hostowane w repo, `/assets/kategorie/…`) — ładuje się
ZAWSZE, bez sieci i bez tokenów. Warunek: `kategoria` artykułu musi **dokładnie**
pasować do nazwy z `config.yaml` (patrz KROK 2). To jest gwarancja obrazu.

**Opcjonalnie** podaj `obraz.query`: **precyzyjną, ANGIELSKĄ frazę** (2–5 słów)
wskazującą konkretny, fotografowalny obiekt tematu — przeglądarka czytelnika spróbuje
wtedy w tle podmienić zdjęcie kategorii na trafniejsze z Wikimedia Commons. To czysty
bonus: jak się uda, obraz jest konkretniejszy; jak nie — zostaje zdjęcie kategorii.
**Nie rób dla tego researchu ani wywołań sieciowych** — po prostu wpisz dobrą frazę
z głowy (lub `""`, jeśli brak oczywistego obiektu).

Dobre `obraz.query` = **JEDEN konkretny obiekt** (2–4 słowa), nie kombinacja pojęć.
Wyszukiwarka Wikimedia traktuje słowa jako AND — fraza wielotematyczna zwraca
0 wyników i artykuł zostaje przy zdjęciu kategorii. Test: „czy istnieje zdjęcie,
które ktoś podpisałby dokładnie tak?”
- osoba: `Jerome Powell`, `Donald Tusk`, `Sam Altman`
- miejsce/budynek: `Warsaw Stock Exchange`, `Federal Reserve building`, `Strait of Hormuz`
- rzecz/logo: `Leopard 2 tank`, `NVIDIA logo`, `James Webb Space Telescope`
❌ abstrakty (`inflation`, `economy growth`)
❌ kombinacje pojęć (`Shein Temu parcels customs Europe`,
   `European farmers tractor protest fertilizer` — 0 wyników; lepiej:
   `Temu parcel`, `tractor protest Brussels`).

**Research wtórny (poza listą źródeł) — tryb WYJĄTKOWY** (`research_wtorny.tryb`
w configu: `nigdy` | `wyjatkowo` | `swobodnie`). Przy `wyjatkowo` wolno z niego
skorzystać TYLKO w dwóch przypadkach:
- **(a)** w materiale źródłowym brakuje naprawdę istotnej informacji, bez której
  artykuł byłby niepełny lub mylący;
- **(b)** informacje źródła wydają się nierzetelne lub sprzeczne i wymagają
  weryfikacji.
NIE używaj go do wzbogacania kontekstu, zbierania danych do wykresu ani
wydłużania akapitów. Stały wyjątek: bieżący kurs walut do przeliczeń na PLN
(KROK 2). Każde użycie zaloguj:
`log("info", "Research wtórny: <artykuł> — <powód (a)/(b)>")`.
Źródło wtórne nigdy nie jest linkiem artykułu (`zrodlo.url`); jeśli jego treść
trafiła do akapitów, wypisz je w `zrodla_dodatkowe` (KROK 2).

## KROK 2 — Redakcja

- **`kategoria` — DOKŁADNA nazwa z `config.yaml`:** wpisuj po polsku, znak w znak
  (np. `Wojna`, nie `Война`/`War`; `Ciekawostka na dziś` w całości). Od tego zależy
  zdjęcie kategorii i filtr w navbarze. Zła nazwa = błąd w Logs i domyślne zdjęcie.
- **Tytuł:** rzeczowy, bez emocji (❌ „Gigantyczny krach!” → ✅ „S&P 500 spadł o 2,3%”).
- **`zrodlo.opublikowano` — timestamp publikacji U ŹRÓDŁA:** data i godzina,
  kiedy źródło opublikowało informację, format `"19.07.2026 06:45"` (czas polski,
  24h). Wyniki wyszukiwania zwykle podają czas publikacji („3 hours ago”, datę) —
  przelicz na konkretny timestamp. Gdy znasz tylko datę — samo `"19.07.2026"`.
  Nie zgaduj co do minuty; lepsza sama data niż zmyślona godzina. Gazeta pokaże
  to przy artykule (czytelnik widzi, jak świeży jest news).
- **`skrot` — jedno zdanie do sekcji „W skrócie”:** każdy artykuł ma pole `skrot`
  (≤ 20 słów) — samodzielne, rzeczowe streszczenie z najważniejszą liczbą, jeśli
  jest. Gazeta pokazuje je jako listę na górze wydania z linkami do artykułów.
  Bez markerów `{{...}}` i bez powtarzania tytułu słowo w słowo.
- **Liczba akapitów = `wydanie.akapity` z `config.yaml`** (gdy brak pola — 3).
  Dokładnie tyle w każdym artykule. Struktura: pierwszy = najważniejsze fakty
  i liczby; środkowe = kontekst, szczegóły, reakcje; ostatni = dlaczego to
  ważne / konsekwencje. Dodatkowe akapity wypełniaj kontekstem i analizą
  z JUŻ zebranego materiału — nie rób dodatkowego researchu tylko po to,
  by wydłużyć artykuł.
- **Ton:** obiektywny, agencyjny, zero marketingu.
- **Trudne terminy — marker `{{termin|wyjaśnienie}}` w akapitach.** Czytelnik to
  programista: żargon branżowy spoza IT (finanse, wojskowość, prawo, nauka), mało
  znane miejscowości, instytucje czy instrumenty oznaczaj w treści akapitu
  markerem `{{...|...}}` — gazeta pokaże podkreślenie z tooltipem po
  najechaniu/kliknięciu. Zasady:
  - wyjaśnienie krótkie (≤ 12 słów), po polsku, bez kropki na końcu;
  - termin wpisuj w odmianie, w jakiej stoi w zdaniu (np.
    `{{kontraktach terminowych|umowy kupna/sprzedaży z ustaloną ceną i przyszłą datą}}`);
  - oznaczaj tylko PIERWSZE wystąpienie, maksymalnie ~3 na artykuł;
  - nie oznaczaj rzeczy oczywistych (USA, NATO, inflacja, GPU) ani niczego
    w tytułach i `kluczowe_liczby` — marker działa tylko w `akapity`.
- **Sprzeczne narracje między źródłami:** gdy źródła opisują ten sam news inaczej,
  fakty wspólne dla wszystkich pisz wprost, a rozbieżne twierdzenia i interpretacje
  atrybuuj z nazwy w treści akapitu — np. „Bankier podaje, że…, natomiast Al Jazeera
  opisuje to jako…”. Nie wybieraj po cichu jednej narracji. Przy sprzecznych
  **liczbach** wybierz źródło oficjalne / bliższe zdarzenia i zaloguj rozbieżność
  (KROK 2.5).
- **Wiele źródeł w artykule:** jeśli treść akapitów pochodzi z więcej niż jednego
  źródła (inne źródło pierwotne albo research wtórny), wypisz WSZYSTKIE dodatkowe
  w polu `zrodla_dodatkowe: [{"nazwa": "...", "url": "..."}]` — gazeta pokaże je
  przy artykule obok źródła bazowego. `zrodlo` pozostaje głównym źródłem
  pierwotnym (link tytułu). Gdy całość pochodzi z jednego źródła — pomiń pole.
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
- **wykres — TYLKO gdy źródło samo daje komplet danych.** Dodaj wykres wyłącznie
  wtedy, gdy artykuł źródłowy sam prezentuje wykres albo podaje dane, które da
  się wprost przedstawić na wykresie lub w tabeli (np. seria notowań, wartości
  rok po roku). **NIE doszukuj danych osobnym researchem** — brak kompletu =
  brak wykresu, bez żalu (to normalna sytuacja, nie loguj jej). Przy kategorii
  z `wykres: nie` — pomiń zawsze. Nie wymyślaj i nie interpoluj danych.
  - `typ` = `"linia"` lub `"slupki"`; etykiety (`etykiety`) dla każdego punktu.
  - Liczba punktów = tyle, ile daje źródło. Jeśli daje 8–15 — świetnie (wykres
    jest interaktywny, gęste dane wyglądają najlepiej), ale 4 realne punkty ze
    źródła > 10 doszukanych.
  - Dodaj `jednostka` (np. `"%"`, `" pkt"`, `" USD"`, `" mld"`) — pokaże się w
    tooltipie i na osi Y.

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
- **Problemy z danymi** — rozbieżne wartości między źródłami, brak aktualnego
  kursu walutowego do przeliczenia na PLN. (Brak danych do wykresu NIE jest
  zdarzeniem — po prostu pomiń wykres, patrz KROK 2.)
- **Info** — istotne decyzje redakcyjne, obejścia, nietypowe sytuacje warte uwagi.

**NIE loguj obrazów.** Zdjęcie kategorii ładuje się zawsze (repo, ten sam origin),
a podmiana na Wikimedia to cichy best-effort w przeglądarce czytelnika —
„nierozwiązany obraz” nie istnieje w tej architekturze i nie jest zdarzeniem.

Zasady: notuj **konkretnie** (kategoria, artykuł, dosłowny komunikat błędu, URL
pomocy jeśli był). Nie loguj rzeczy oczywistych ani szumu. Jeśli wszystko poszło
gładko — zostaw `logi` puste (gazeta pokaże „Brak zdarzeń”). Część logów skrypt
z KROK 3 dopisze automatycznie (złe nazwy kategorii, rozbieżność liczby
artykułów i akapitów).

**Higiena logów — publikowane są tylko logi z OSTATNIEGO, poprawnego przebiegu:**
- Jeśli uruchamiasz skrypt KROK 3 kilka razy (poprawki, debug), lista `logi`
  za każdym razem startuje od zera — **nie przenoś** wpisów z nieudanych prób.
- Wpis o problemie, który NAPRAWIŁEŚ przed publikacją (np. poprawiona nazwa
  kategorii), **usuń** — czytelnika interesuje stan opublikowanego wydania.
- **Nie pisz własnych logów kontrolnych** (liczba akapitów, liczba artykułów,
  nazwy kategorii) — te kontrole skrypt loguje sam i tylko przy rozbieżności.
- Używaj skryptu z instrukcji **bez przerabiania logiki kontroli**.

## KROK 3 — Wygeneruj plik wydania

W poniższym skrypcie **ustaw `WYDANIE`** na wartość z promptu (`rano` albo `wieczor`),
zbuduj listę `artykuly` (w kolejności kategorii z configu), **dopisz `log(...)`
dla problemów z KROK 1–2** (patrz KROK 2.5) i uruchom:

```python
import json, pathlib, subprocess, datetime, re
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
  "logi": [],      # <-- zdarzenia z uruchomienia rutyny -> sekcja „Logs” w gazecie (patrz KROK 2.5)
  "pogoda": cfg.get('pogoda') or {}  # lokalizacja + link prognozy z configu (pasek w nagłówku)
}

# --- Pogoda z Interii: parsowanie HTML w skrypcie (zero tokenów LLM).
#     Gdy się nie uda — pole zostaje puste, przeglądarka użyje Open-Meteo. ---
import urllib.request
try:
    _pu = dane["pogoda"].get("prognoza_url", "")
    if "pogoda.interia.pl" in _pu:
        _rq = urllib.request.Request(_pu, headers={"User-Agent": "Mozilla/5.0"})
        _h = urllib.request.urlopen(_rq, timeout=15).read().decode("utf-8", "ignore")
        _t = re.search(r'weather-currently-temp-strict">\s*(-?\d+)°C', _h)
        _o = re.search(r'weather-currently-icon[^"]*"\s*\n?\s*title="([^"]+)"', _h)
        if _t:
            _op = (_o.group(1) if _o else "").strip()
            _l = _op.lower()
            _e = ("⛈️" if "burz" in _l else "🌧️" if "deszcz" in _l or "opady" in _l else
                  "🌨️" if "śnieg" in _l else "🌫️" if "mgł" in _l else
                  "☀️" if "słonecznie" in _l or "bezchmurnie" in _l else
                  "🌤️" if "małe" in _l else "⛅" if "umiarkowane" in _l else
                  "☁️" if "zachmurzenie" in _l or "pochmurno" in _l else "")
            dane["pogoda"]["aktualna"] = f"{dane['pogoda'].get('miasto','')} {_e} {_t.group(1)}°C".replace("  ", " ").strip()
            if _op: dane["pogoda"]["opis"] = _op
except Exception as _ex:
    log("info", f"Pogoda z Interii nieudana ({_ex}) — przeglądarka użyje Open-Meteo.")

def log(poziom, wiadomosc):
    """Dodaj wpis do sekcji „Logs”. poziom: 'error' | 'warning' | 'info'."""
    dane["logi"].append({"poziom": poziom, "wiadomosc": wiadomosc})
    print(f"  LOG[{poziom}] {wiadomosc}")

# >>> Wklej tu wpisy log(...) dla problemów napotkanych w KROK 1–2 (patrz KROK 2.5),
#     np. log("error", "API Error: 400 ... domains not accessible ... ['reuters.com'] ...")

# --- Obrazy: rutyna NIE pobiera zdjęć (to zawsze padało na IP datacenter i marnowało
#     czas oraz tokeny). Każdy artykuł dostaje w przeglądarce zdjęcie SWOJEJ KATEGORII
#     hostowane w repo (/assets/kategorie/…) — ten sam origin, więc ZAWSZE się ładuje.
#     Jeśli podasz `obraz.query` (konkretna fraza EN), przeglądarka spróbuje w tle
#     podmienić je na trafniejsze zdjęcie z Wikimedia Commons — czysty best-effort,
#     bez wpływu na niezawodność. Tu tylko porządkujemy pole `obraz`. ---
for a in dane["artykuly"]:
    obraz = a.get("obraz") or {}
    a["obraz"] = {"query": obraz.get("query") or "", "alt": obraz.get("alt") or a["tytul"]}

# --- Kontrola: kategorie muszą DOKŁADNIE pasować do config.yaml (łapie np. „Война”->„Wojna”) ---
valid_cats = {k['nazwa'] for k in cfg['kategorie']}
for a in dane["artykuly"]:
    if a["kategoria"] not in valid_cats:
        log("error", f"Nieznana kategoria „{a['kategoria']}” (artykuł „{a['tytul']}”). Użyj DOKŁADNEJ nazwy z config: {sorted(valid_cats)}.")

# --- Kontrola: liczba akapitów wg config (wydanie.akapity, domyślnie 3) ---
n_akapity = cfg['wydanie'].get('akapity', 3)
for a in dane["artykuly"]:
    if len(a.get("akapity") or []) != n_akapity:
        log("warning", f"Artykuł „{a['tytul']}”: {len(a.get('akapity') or [])} akapitów, config wymaga {n_akapity}.")

# --- Kontrola: liczba artykułów na kategorię wg config.yaml (rozbieżności -> log) ---
from collections import Counter
oczek = {k['nazwa']: k.get('liczba', 1) for k in cfg['kategorie']}
masz = Counter(a['kategoria'] for a in dane['artykuly'])
for kat, n in oczek.items():
    if masz.get(kat, 0) != n:
        print(f"  ⚠ {kat}: jest {masz.get(kat,0)}, config oczekuje {n}")
        log("warning", f"Kategoria „{kat}”: złożono {masz.get(kat,0)} art., config oczekuje {n}.")
# --- Higiena logów: dedup + wpisy kontrolne tylko dla realnych rozbieżności ---
_seen = set()
dane["logi"] = [l for l in dane["logi"]
                if (l["poziom"], l["wiadomosc"]) not in _seen
                and not _seen.add((l["poziom"], l["wiadomosc"]))]

print(f"Artykułów łącznie: {len(dane['artykuly'])} (config: {sum(oczek.values())})")
print(f"Logów: {len(dane['logi'])}")

out = tpl.replace('__DANE__', json.dumps(dane, ensure_ascii=False, indent=2))
# Wytnij blok demo (Lorem Ipsum do podglądu szablonu) — w wydaniach ma go nie być:
out = re.sub(r'/\* DEMO-START.*?DEMO-END \*/', '/* dane produkcyjne */', out, flags=re.S)
assert '__DANE__' not in out
assert 'DEMO-START' not in out
filename = f"{today}-{WYDANIE}-{now.strftime('%H%M')}.html"
pathlib.Path('/tmp/grzyb_times.html').write_text(out, encoding='utf-8')
print(f'OK — {len(out):,} bajtów | plik: {filename}')
```

Schemat artykułu (`obraz.query` opcjonalna — angielska fraza dla ew. lepszego zdjęcia;
gwarantowane zdjęcie kategorii dostaje artykuł i tak, po `kategoria`):

```json
{
  "kategoria": "Inwestowanie",
  "tytul": "Rzeczowy tytuł z liczbą",
  "skrot": "Jedno zdanie (≤20 słów) do sekcji „W skrócie” — z kluczową liczbą.",
  "zrodlo": {"nazwa": "Bankier", "url": "https://...", "opublikowano": "19.07.2026 06:45"},
  "zrodla_dodatkowe": [{"nazwa": "Al Jazeera", "url": "https://..."}],
  "obraz": {"query": "Warsaw Stock Exchange", "alt": "opis zdjęcia po polsku"},
  "kluczowe_liczby": [{"wartosc": "2,3%", "opis": "spadek indeksu"}],
  "wykres": {"typ": "linia", "tytul": "S&P 500 — 10 sesji", "jednostka": " pkt",
             "etykiety": ["1.07","2.07","3.07","4.07","7.07","8.07","9.07","10.07","11.07","14.07"],
             "wartosci": [6320,6345,6338,6360,6402,6390,6455,6480,6472,6512]},
  "akapity": ["Akapit 1 — fakty, np. z {{backwardacji|sytuacja, gdy cena natychmiastowa przewyższa terminową}}.", "Akapit 2 — kontekst i szczegóły.", "Akapit 3 — konsekwencje."],
  "kontynuacja": false
}
```

Liczba elementów `akapity` = `wydanie.akapity` z configu (domyślnie 3).

`zrodla_dodatkowe` — tylko gdy treść faktycznie korzysta z więcej niż jednego
źródła (patrz KROK 2); przy jednym źródle pomiń pole.

`kontynuacja: true` **tylko** gdy artykuł rozwija temat z poprzedniego wydania
(patrz KROK 1 — deduplikacja); wtedy gazeta pokazuje badge „Aktualizacja”.
Przy zwykłych, nowych tematach pole pomiń albo ustaw `false`.

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

# Grupowanie po dniach (najnowszy dzień pierwszy; w dniu wieczór przed rankiem — jak w `files`)
from collections import OrderedDict
dni = OrderedDict()
for e in editions: dni.setdefault(e['date'], []).append(e)
cards = ''.join(
    f'<div class="day"><div class="day-head">{date}</div>' + ''.join(
        f'<a href="{e["url"]}" class="item{" item--latest" if e["first"] else ""}">'
        + f'<span class="item-label">{e["icon"]} {e["label"]}{"<span class=badge>Najnowsze</span>" if e["first"] else ""}</span>'
        + '<span class="item-go">Czytaj &rarr;</span></a>' for e in items) + '</div>\n'
    for date, items in dni.items()
)
html = '''<!DOCTYPE html>
<html lang="pl"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Grzyb Times — archiwum</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,700;9..144,900&family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
<style>
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
.day{margin-top:30px}
.day-head{font-family:Fraunces,serif;font-weight:700;font-size:1.05em;padding-bottom:8px;margin-bottom:10px;
  border-bottom:1px solid var(--rule)}
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
@media(max-width:600px){body{padding:32px 14px 60px}.item{padding:11px 12px}.item-go{display:none}}
</style></head>
<body><div class="wrap">
<header><div class="kicker">Archiwum wydań</div><h1><a href="/">Grzyb Times</a></h1>
<div class="bar">Redagowane przez AI &middot; wydania poranne i wieczorne</div></header>
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
