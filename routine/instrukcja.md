# Instrukcja generowania wydania „Grzyb Times”

Jesteś profesjonalnym edytorem i researcherem. Wygeneruj jedno wydanie gazety
**Grzyb Times** i opublikuj je na GitHub Pages (`kapitanski-dev/kapitanski-dev.github.io`).

Parametr **`WYDANIE`** (`rano` albo `wieczor`) pochodzi z promptu rutyny, która Cię
uruchomiła. Trzymaj się tej instrukcji dokładnie — cała konfiguracja, szablon
i mechanika są w repo.

| WYDANIE | kicker / numer | ikona w archiwum | zakres |
|---|---|---|---|
| `rano`    | „Wydanie poranne”   | ☀️ | poranne notowania/newsy |
| `wieczor` | „Wydanie wieczorne” | 🌙 | popołudniowe/wieczorne podsumowanie |

**Twoja rola kończy się na treści.** Piszesz JEDEN plik z danymi redakcji (JSON),
a `routine/buduj_wydanie.py` robi resztę: nagłówek wydania, pogodę, obrazy,
kontrole jakości, metryki i podstawienie do szablonu. Nie przepisuj tego skryptu
i nie buduj HTML-a ręcznie.

## KROK 0 — Repo i konfiguracja

Repozytorium jest już sklonowane w środowisku. Zlokalizuj je i postaw znacznik startu:

```bash
date +%s > /tmp/grzyb_start_epoch   # „czas wykonania” w sekcji Logs
REPO=$(find /home /root /workspace /tmp -maxdepth 6 -name ".git" 2>/dev/null | grep -v '/.git/' | head -1 | xargs dirname 2>/dev/null)
echo "Repo: $REPO" && ls "$REPO"
```

Przeczytaj `"$REPO/config.yaml"` (narzędzie Read). Stamtąd pochodzą: tytuł gazety,
lista kategorii (kolejność = ważność, pierwsza = okładka), **`liczba` artykułów
w każdej kategorii**, **`wydanie.akapity`** (limit akapitów na artykuł),
`zrodla_pierwotne` i tryb researchu wtórnego. **Nie zgaduj — użyj wartości z pliku.**
Łączna liczba artykułów wydania = suma pól `liczba`.

## KROK 0.5 — Uwagi czytelników (GitHub Issues)

Czytelnicy zgłaszają uwagi przyciskiem „Zgłoś uwagę” (issue z tytułem `[Uwaga] …`).
Pobierz otwarte zgłoszenia — jedno tanie wywołanie, publiczne API bez tokena:

```bash
curl -s "https://api.github.com/repos/kapitanski-dev/kapitanski-dev.github.io/issues?state=open&per_page=20" \
 | python3 -c "import json,sys; [print('-', i['title'], '::', (i.get('body') or '')[:300].replace(chr(10),' ')) for i in json.load(sys.stdin) if i['title'].startswith('[Uwaga]')]"
```

- **Uwzględnij zasadne uwagi** (błąd merytoryczny, prośba o temat/doprecyzowanie)
  w bieżącym wydaniu i zaloguj każdą: `{"poziom": "info", "wiadomosc": "Uwaga czytelnika uwzględniona: <tytuł> — <co zrobiono>"}`.
- Uwagę bezzasadną lub nie na teraz pomiń bez logowania.
- **Nie odpowiadaj na issue i nie zamykaj ich** — to robi użytkownik.
- Brak zgłoszeń = idź dalej, nic nie loguj.

## KROK 1 — Research

Użyj WebSearch. Dla **każdej** kategorii z `config.yaml` (w kolejności) znajdź
**dokładnie tyle artykułów, ile wynosi jej `liczba`** — z domen z `zrodla_pierwotne`,
w oknie świeżości (niżej). Gdy sensownych materiałów jest mniej, daj mniej: nie
duplikuj tematów, nie wychodź poza listę źródeł, nie dopychaj wodą.

### Świeżość — okno liczone od poprzedniego wydania

Wydanie ma pokrywać to, co wydarzyło się **od poprzedniego wydania**. Skrypt liczy
okno sam (czas od ostatniego pliku w `wydania/` + 2 h zapasu, w granicach 12–36 h):
przy dwóch wydaniach dziennie wychodzi ~12 h, przy jednym ~24 h. Weekend + kategoria
**Inwestowanie**: co najmniej 48 h (giełdy zamknięte — podsumowania tygodnia, zapowiedzi).

- **To TWARDY warunek.** Wiek liczy się datą WYDARZENIA / publikacji źródła
  (`zrodlo.opublikowano`), nie datą, w której news wypłynął w wyszukiwarce.
  Uchwała sprzed dwóch tygodni to nie news dnia, nawet jeśli akurat pojawił się
  o niej wpis (wpadka 22.07: rezolucja PE z 08.07 trafiła do wydania).
- **Okno obowiązuje KAŻDĄ kategorię — także Ciekawostkę i Naukę.** Nie ma tematów
  „ponadczasowych”: odkrycie, rekord i ciekawostka też mają datę publikacji
  (wpadka 22.07: rekin goblin sprzed 14 dni i „pszczoły potu” z kwietnia).
- Gdy w kategorii nie ma nic w oknie — daj mniej artykułów. Nie łataj luki starym tematem.
- Skrypt raportuje wiek źródeł **zbiorczo**; nie loguj tego ręcznie.

### `zrodlo.opublikowano` — pełna data i czas

Tak dokładnie, jak podaje źródło: `DD.MM.YYYY GG:MM:SS`, `DD.MM.YYYY GG:MM` albo
`DD.MM.YYYY`. Czas polski, 24 h. Nigdy sam miesiąc/rok („2026-07”) — bez pełnej daty
nie da się ocenić okna. Źródło nie podaje daty w ogóle? Pomiń pole, nie zgaduj.

### `zrodlo.url` — KOPIUJ 1:1 z wyników wyszukiwania

Najdroższa wpadka gazety: czytelnik klika i dostaje 404 albo stronę główną
(audyt 29.07: link Al Jazeery = 404, dwa artykuły linkowały `https://www.sciencedaily.com/`).

- Adres bierz **dosłownie z wyniku WebSearch/WebFetch**. **Nigdy** nie składaj go
  z wzorca domeny, nie zgaduj slugu ani numeru artykułu, nie skracaj, nie dopisuj daty.
- Nie ma w wynikach pełnego adresu artykułu? **Zmień temat albo źródło.** Strona
  główna, kategoria serwisu i wyszukiwarka NIE są linkiem artykułu.
- Skrypt sprawdza ścieżkę adresu i domenę względem `zrodla_pierwotne` — jedno i drugie
  raportuje jako `error`.

### Paywall

Link za twardym paywallem (**bloomberg.com**) jest dla czytelnika bezwartościowy.
Gdy temat jest w kilku źródłach z listy, na `zrodlo.url` daj wersję bez paywalla,
a paywallowaną dopisz do `zrodla_dodatkowe`. Bloomberg jako `zrodlo.url` — tylko gdy
temat jest WYŁĄCZNIE tam. Skrypt ostrzega, gdy paywall przekroczy 1/3 wydania.

### Jak wybierać, gdy kandydatów jest więcej niż `liczba`

Oceń kandydatów w myślach (nie wypisuj punktacji — szkoda tokenów) wg trzech kryteriów:

1. **Realny skutek (waga 3)** — jak duży i trwały wpływ na ludzi, gospodarkę, rynki.
   Fakty i podjęte decyzje > zapowiedzi, spekulacje, komentarze.
2. **Skala i zasięg (waga 2)** — ilu ludzi / jak duży kapitał / ile krajów. Globalne >
   lokalne (chyba że temat wprost dotyczy Polski).
3. **Nowość i przełomowość (waga 1)** — rzeczy bez precedensu > kolejny odcinek znanej historii.

Weź top `liczba` i uporządkuj malejąco. Remisy rozstrzygaj na korzyść konkretu
(zweryfikowane liczby, podjęte decyzje) przeciw „może / planuje / rozważa”.

### Różnorodność w kategorii

Gdy kategoria obejmuje kilka RÓWNOLEGLE aktywnych wątków (typowo **Wojna**: Bliski
Wschód, Ukraina–Rosja), rozłóż sloty `liczba` między odrębne fronty — czytelnik ma
dostać przekrój, a nie 3 odcinki tej samej wojny (wpadka 22.07 wieczór: trzy warianty
jednego wątku, a świeży atak na rosyjskie magazyny wypadł). Jeśli pierwszy WebSearch
skupił się na jednym froncie, zrób **jedno celowane wyszukanie** drugiego — dopiero
potem wybieraj.

### Okładka

Pierwsza kategoria (`liczba: 1`): JEDNA, absolutnie najważniejsza wiadomość dnia
z dowolnego tematu — „news numer jeden”. **Nie powielaj jej w żadnej innej kategorii**;
jeśli najważniejszy news jest polityczny, w kategorii Polityka daj inne tematy.

### Deduplikacja względem poprzedniego wydania (OBOWIĄZKOWA)

Zanim zaczniesz research, przeczytaj NAJNOWSZY plik z `"$REPO/wydania/"` (sortowanie
po nazwie) i wynotuj jego tematy — tytuły i kategorie z JSON-a w `<script id="dane-gazety">`.
To czytanie lokalne, nie kosztuje tokenów sieci.

- **Nie powtarzaj newsa z poprzedniego wydania**, jeśli nie wydarzyło się nic nowego.
- **Temat wolno kontynuować tylko z wartością dodaną**: nowe fakty, liczby, reakcje,
  skutki. Artykuł-kontynuacja zaczyna się od tego, co NOWE (nie streszczaj od zera),
  a w drugim akapicie krótko nawiązuje do poprzedniego stanu („po wczorajszym…”).
  Ustaw wtedy **`"kontynuacja": true`** — gazeta pokaże badge „Aktualizacja”.
- Odrzucenie tematu przez duplikację jest normalne i nie wymaga logu; zaloguj tylko,
  gdy przez deduplikację nie dało się wypełnić `liczba` kategorii.

### Wątki do sprawdzenia (follow-up — OBOWIĄZKOWY)

JSON poprzedniego wydania ma pole `watki` — listę zapowiedzianych wydarzeń, o których
pisaliśmy (testy, starty, głosowania, decyzje, wyniki). Dla KAŻDEGO sprawdź w researchu,
czy się rozstrzygnął:

- **rozstrzygnął się** → mocny kandydat na artykuł (`kontynuacja: true`), w rubryce
  oceny traktuj priorytetowo — obiecaliśmy czytelnikowi ciąg dalszy. (Wpadka, której to
  zapobiega: 16.07 zapowiedzieliśmy start Starship Flight 13, start odwołano, a gazeta
  nigdy do tematu nie wróciła.)
- **wciąż otwarty** → przepisz do `watki` bieżącego wydania;
- **stracił aktualność / starszy niż 7 dni** → porzuć.

Po redakcji zbuduj `watki` bieżącego wydania — każda zapowiedź przyszłego wydarzenia
to jeden obiekt:

```json
{"data": "2026-07-31", "temat": "Starship Flight 13", "sprawdzic": "czy start się odbył i z jakim skutkiem"}
```

`data` w formacie `RRRR-MM-DD`. Gdy termin jest tylko przybliżony, wpisz `null`,
a określenie czasu daj słownie w `temat` (np. `"Wyniki NVIDIA — sierpień 2026"`).
Maksymalnie ~6 wątków, najważniejsze. Te wpisy zasilają też stronę `kalendarz.html`,
więc `temat` pisz zwięźle, po ludzku i bez technicznych slugów (`meta-q2-2026` ❌).

### Oszczędzaj tokeny

- Celuj w **1 WebSearch na kategorię** (ewentualnie 1 dodatkowe, gdy pierwsze nie
  wystarczyło). Nie przeszukuj w kółko tego samego.
- **`WebFetch` tylko wtedy, gdy naprawdę musisz** odczytać konkretne liczby lub cytat,
  których nie ma w wynikach wyszukiwania. Nie pobieraj stron „na zapas”.
- **Nie odpytuj domen, które blokują bota** (błąd 400 „domain not accessible”).
  Trafisz na taką — zaloguj i pomiń, nie ponawiaj.
- Wykres buduj z danych, które już masz ze źródła; jeśli wymagałby osobnego researchu, pomiń go.

### Research wtórny (poza listą źródeł) — tryb WYJĄTKOWY

Przy `research_wtorny.tryb: wyjatkowo` wolno z niego skorzystać TYLKO gdy:
**(a)** w materiale źródłowym brakuje istotnej informacji, bez której artykuł byłby
niepełny lub mylący, albo **(b)** informacje źródła wydają się nierzetelne/sprzeczne
i wymagają weryfikacji. NIE do wzbogacania kontekstu, danych do wykresu ani wydłużania
akapitów. Stały wyjątek: bieżący kurs walut do przeliczeń na PLN.

Każde użycie zaloguj (`info`: „Research wtórny: <artykuł> — <powód (a)/(b)>”). Źródło
wtórne nigdy nie jest linkiem artykułu; jeśli jego treść trafiła do akapitów, wypisz
je w `zrodla_dodatkowe`.

### Obrazy — NIE zajmujesz się nimi (żadnych wywołań narzędzi)

Warstwy są automatyczne: skrypt próbuje pobrać **og:image** artykułu źródłowego,
a gdy się nie uda, artykuł dostaje zdjęcie **swojej kategorii** z `/assets/kategorie/`
(ładuje się zawsze — warunek: `kategoria` dokładnie jak w `config.yaml`). **Uwaga:
środowisko rutyny nie ma wyjścia HTTP w świat, więc og:image w praktyce nie działa
od 20.07.2026** — realnym obrazem jest zdjęcie kategorii, a jedyną szansą na coś
trafniejszego jest podmiana z Wikimedia Commons w przeglądarce czytelnika. Dlatego
`obraz.query` warto wypełnić dobrze.

**Okładka — OBOWIĄZKOWE `obraz.kategoria`.** Kategoria „Okładka” nie ma własnego
zdjęcia, a jej glob nie pasuje do niczego konkretnego (wpadka 20.07: wojna USA–Iran
zilustrowana kulą ziemską). W artykule okładkowym wpisz w `obraz.kategoria` DOKŁADNĄ
nazwę kategorii z configu, do której news tematycznie należy (np. `"Wojna"`).
W pozostałych artykułach tego pola NIE dodawaj.

**`obraz.query`** — precyzyjna, ANGIELSKA fraza (2–4 słowa) wskazująca konkretny,
fotografowalny obiekt. Nie rób dla niej researchu ani wywołań sieciowych — wpisz
z głowy (lub `""`, gdy brak oczywistego obiektu). Wyszukiwarka Wikimedia traktuje
słowa jako AND, więc fraza wielotematyczna zwraca 0 wyników; przy braku trafień
przeglądarka skraca frazę od KOŃCA, więc **najważniejsze słowa dawaj na początku**.
Test: „czy istnieje zdjęcie, które ktoś podpisałby dokładnie tak?”

- ✅ osoba: `Jerome Powell` · miejsce: `Strait of Hormuz` · rzecz: `Leopard 2 tank`, `NVIDIA logo`
- ❌ abstrakty (`inflation`, `economy growth`)
- ❌ kombinacje pojęć (`Shein Temu parcels customs Europe` → 0 wyników; lepiej `Temu parcel`)

## KROK 2 — Redakcja

- **`kategoria` — DOKŁADNA nazwa z `config.yaml`**, po polsku, znak w znak (np. `Wojna`,
  nie `Война`/`War`; `Ciekawostka na dziś` w całości). Od tego zależy zdjęcie kategorii
  i filtr w navbarze.
- **Tytuł:** rzeczowy, bez emocji (❌ „Gigantyczny krach!” → ✅ „S&P 500 spadł o 2,3%”).
- **`skrot`** — jedno samodzielne zdanie (≤ 20 słów) do sekcji „W skrócie”, z najważniejszą
  liczbą, jeśli jest. Bez markerów `{{...}}`, bez powtarzania tytułu słowo w słowo.
- **Liczba akapitów: CEL i górna granica = `wydanie.akapity`.** Pisz tyle, ile pozwala
  materiał; za mało treści → daj MNIEJ, bez wody i bez dodatkowego researchu. Nigdy więcej
  niż limit. Struktura: pierwszy = najważniejsze fakty i liczby; środkowe = kontekst,
  szczegóły, reakcje; ostatni = dlaczego to ważne / konsekwencje.
- **Ton:** obiektywny, agencyjny, zero marketingu.
- **Trudne terminy — marker `{{termin|wyjaśnienie}}` w akapitach.** Czytelnik jest
  programistą: żargon spoza IT (finanse, wojskowość, prawo, nauka), mało znane miejscowości,
  instytucje i instrumenty oznaczaj markerem — gazeta pokaże tooltip. Zasady:
  wyjaśnienie ≤ 12 słów, po polsku, bez kropki; termin w odmianie ze zdania; tylko
  PIERWSZE wystąpienie, maks. ~3 na artykuł; **nazwane reguły, ustawy, dyrektywy
  i doktryny mają PIERWSZEŃSTWO** (reguła Volckera, Basel III, MiCA — czytelnik nie
  wywnioskuje ich z kontekstu); nie oznaczaj oczywistości (USA, NATO, inflacja, GPU)
  ani niczego poza `akapity`.
- **Sprzeczne narracje:** fakty wspólne dla źródeł pisz wprost, a rozbieżne twierdzenia
  atrybuuj z nazwy w treści („Bankier podaje, że…, natomiast Al Jazeera opisuje…”).
  Nie wybieraj po cichu jednej narracji. Przy sprzecznych **liczbach** wybierz źródło
  oficjalne / bliższe zdarzenia i zaloguj rozbieżność.
- **Wiele źródeł:** gdy akapity korzystają z więcej niż jednego źródła, wypisz wszystkie
  dodatkowe w `zrodla_dodatkowe`. `zrodlo` pozostaje głównym źródłem (link tytułu).
- **Kwoty — ZAWSZE waluta + PLN w nawiasie:** każdą kwotę w tytule i akapitach podaj
  w walucie oryginalnej, a po niej przybliżoną wartość w złotych po aktualnym kursie,
  z tyldą: „Apple wyceniono na 4,9 bln USD (~19,6 bln zł)”. Kurs pobierz raz w researchu
  i użyj spójnie w całym wydaniu; zaloguj go (`info`). Kwota podana już w PLN —
  nie przeliczaj. Ta sama zasada w `kluczowe_liczby`.
- **`kluczowe_liczby`:** 1–3 najważniejsze wartości liczbowe artykułu.
- **`wykres` — TYLKO gdy źródło samo daje komplet danych** (seria notowań, wartości rok
  po roku). **Nie doszukuj danych osobnym researchem** — brak kompletu = brak wykresu
  (normalna sytuacja, nie loguj jej). Kategoria z `wykres: nie` — pomiń zawsze. Nie
  wymyślaj i nie interpoluj. `typ`: `"linia"` albo `"slupki"`; etykieta dla każdego punktu;
  dodaj `jednostka` (np. `"%"`, `" pkt"`, `" USD"`). 4 realne punkty ze źródła > 10 doszukanych.

### Schemat artykułu

```json
{
  "kategoria": "Inwestowanie",
  "tytul": "Rzeczowy tytuł z liczbą",
  "skrot": "Jedno zdanie (≤20 słów) do sekcji „W skrócie” — z kluczową liczbą.",
  "zrodlo": {"nazwa": "Bankier", "url": "https://...", "opublikowano": "19.07.2026 06:45:12"},
  "zrodla_dodatkowe": [{"nazwa": "Al Jazeera", "url": "https://..."}],
  "obraz": {"query": "Warsaw Stock Exchange", "alt": "opis zdjęcia po polsku"},
  "kluczowe_liczby": [{"wartosc": "2,3%", "opis": "spadek indeksu"}],
  "wykres": {"typ": "linia", "tytul": "S&P 500 — 10 sesji", "jednostka": " pkt",
             "etykiety": ["1.07","2.07","3.07","4.07","7.07"],
             "wartosci": [6320,6345,6338,6360,6402]},
  "akapity": ["Akapit 1 — fakty, np. z {{backwardacją|sytuacja, gdy cena natychmiastowa przewyższa terminową}}.", "Akapit 2 — kontekst.", "Akapit 3 — konsekwencje."],
  "kontynuacja": false
}
```

Pola opcjonalne (`zrodla_dodatkowe`, `wykres`, `kontynuacja`, `obraz.kategoria`) pomijaj,
gdy nie mają zastosowania.

## KROK 2.5 — Logi (sekcja „Logs” w gazecie)

Przez całe wykonanie notuj zdarzenia, które pomogą ulepszać gazetę, i wpisz je do pola
`logi` w danych redakcji jako `{"poziom": "error"|"warning"|"info", "wiadomosc": "..."}`.

**Co logować:**

- **Błędy narzędzi** — dosłowną treść, np. `"API Error: 400 The following domains are not
  accessible to our user agent: ['reuters.com']…"`.
- **Źródło niedostępne / zablokowane**, przekierowania, paywall, timeouty.
- **Problemy z danymi** — rozbieżne wartości między źródłami, brak kursu walutowego.
- **Info** — kurs użyty w wydaniu, istotne decyzje redakcyjne, obejścia, nietypowe sytuacje.

**Czego NIE logować** (robi to skrypt, ręczne wpisy tylko dublują):

- świeżości źródeł, liczby artykułów w kategorii, liczby akapitów, nazw kategorii,
  poprawności linków, czasu wykonania i zużycia tokenów;
- obrazów — zdjęcie kategorii ładuje się zawsze, a podmiana z Wikimedia to cichy
  best-effort w przeglądarce; „nierozwiązany obraz” nie istnieje w tej architekturze;
- braku danych do wykresu — to normalna sytuacja, nie zdarzenie.

**Higiena:** publikujemy logi z jednego, poprawnego przebiegu. Uruchamiasz skrypt kilka
razy? Lista startuje od zera — nie przenoś wpisów z nieudanych prób. Problem, który
NAPRAWIŁEŚ przed publikacją, usuń: czytelnika interesuje stan opublikowanego wydania.
Wszystko poszło gładko — zostaw `logi` puste (gazeta pokaże „Brak zdarzeń”).

## KROK 2.7 — Sekcja „Literatura”

Stała rubryka wydania (własny przycisk w pasku filtrów) — lekki, kulturalny kontrapunkt
dla newsów. Buduj ją tylko, gdy `config.yaml → literatura.wlaczona` jest `true`
(inaczej zostaw `"literatura": {}`). Cztery elementy, każdy z pierwszych trzech
z omówieniem na JEDEN akapit. Powiązanie z wydarzeniami dnia jest **opcjonalne** —
nie dopasowuj na siłę; wybieraj rzeczy dobre i ciekawe same w sobie.

1. **Cytat dnia** — myśl znanego autora. Podaj `autor` i (jeśli znasz) `zrodlo` (dzieło)
   albo `"przypisywane"`, gdy atrybucja niepewna. Cytuj wiernie; nie zmyślaj autorstwa.
2. **Przysłowie dnia** — **czysty random, BEZ związku z newsami**. Baza: przysłowie polskie
   (`tresc`, `pochodzenie: "przysłowie polskie"`). W `odpowiedniki` podaj obce wersje
   w stałej kolejności: **angielski (`ang.`), łaciński (`łac.`), japoński (`jp`)** — każdy
   wpis z `jezyk`, `tresc` w oryginale (japoński: zapis oryginalny + transkrypcja
   łacińska w nawiasie) i `tlum` (dosłowne tłumaczenie). **Tylko RZECZYWISTE odpowiedniki** —
   brak trafnego odpowiednika = pomiń język, nie zmyślaj.
3. **Wiersz dnia** — **cały wiersz** (nie fragment), utwór KRÓTKI: fraszka, sonet, krótki
   liryk; łamanie wersów jako `\n`. Pola: `tytul`, `autor`, `tresc`, opcjonalnie `zrodlo_url`.
   **Wiersz podajesz z WŁASNEJ WIEDZY**, tak jak cytat — masz do dyspozycji setki krótkich
   klasyków domeny publicznej, więc wiersz ma być ZAWSZE (pominięcie to absolutna
   ostateczność). wolnelektury.pl to co najwyżej opcjonalna weryfikacja tekstu; jej
   403/niedostępność NIE jest powodem, by pominąć wiersz (audyt 23.07: 403 → wiersz zniknął,
   tak MA NIE być) i nie logujemy tego. ŻELAZNA zasada: **tylko domena publiczna** — autor
   zmarły ponad 70 lat temu. Bezpieczni: Kochanowski, Mickiewicz, Słowacki, Norwid,
   Konopnicka, Asnyk, Leśmian, Tuwim, Horacy. ZAKAZ: Miłosz (†2004), Szymborska (†2012),
   Herbert (†1998), Staff (†1957).
4. **Angielski na dziś** — jedno przydatne `slowo` (z `wymowa` w IPA, `znaczenie` po polsku,
   `przyklad` w formacie `"zdanie EN — tłumaczenie PL"`) oraz jeden idiomatyczny `zwrot`
   (`zwrot_znaczenie`, `zwrot_przyklad` w tym samym formacie). Poziom średnio-zaawansowany,
   słownictwo przydatne przy czytaniu prasy.

Cała sekcja powstaje z **własnej wiedzy** — nie zależy od sieci, więc ma być KOMPLETNA
(4/4) w każdym wydaniu; skrypt ostrzega przy brakach.

```json
{
  "cytat": {"tresc": "Kto nie idzie naprzód, ten się cofa.", "autor": "J.W. Goethe", "zrodlo": "przypisywane", "omowienie": "Jeden akapit — sens myśli."},
  "przyslowie": {"tresc": "Nie ma tego złego, co by na dobre nie wyszło.", "pochodzenie": "przysłowie polskie", "odpowiedniki": [{"jezyk": "ang.", "tresc": "Every cloud has a silver lining", "tlum": "każda chmura ma srebrną podszewkę"}, {"jezyk": "łac.", "tresc": "Per aspera ad astra", "tlum": "przez trudy do gwiazd"}, {"jezyk": "jp", "tresc": "七転び八起き (nana korobi ya oki)", "tlum": "upadaj siedem razy, wstań osiem"}], "omowienie": "Jeden akapit — sens przysłowia."},
  "wiersz": {"tytul": "Tytuł", "autor": "Autor", "tresc": "Cały wiersz,\nwers po wersie.", "omowienie": "Jeden akapit — interpretacja."},
  "angielski": {"slowo": "resilience", "wymowa": "/rɪˈzɪl.jəns/", "znaczenie": "odporność", "przyklad": "The market showed resilience. — Rynek wykazał się odpornością.", "zwrot": "to weather the storm", "zwrot_znaczenie": "przetrwać trudny okres", "zwrot_przyklad": "They weathered the storm. — Przetrwali trudny okres."}
}
```

## KROK 3 — Zapisz dane i zbuduj wydanie

Zapisz **jeden plik** `/tmp/grzyb_dane.json` (narzędzie Write) o strukturze:

```json
{
  "model": "<Twoja dokładna nazwa/ID modelu — wiesz, kim jesteś>",
  "artykuly": [ ... ],
  "literatura": { ... },
  "watki": [{"data": "2026-07-31", "temat": "Starship Flight 13", "sprawdzic": "czy start się odbył"}],
  "logi": [{"poziom": "info", "wiadomosc": "Kurs USD/PLN: 3,79 (money.pl, 29.07.2026)."}]
}
```

Kolejność w `artykuly`: kategorie jak w configu, w obrębie kategorii od najważniejszego.
Pierwszy artykuł (kategoria **Okładka**) otwiera wydanie.

Następnie zbuduj wydanie — podaj WYDANIE z promptu:

```bash
cd "$REPO"
python3 routine/buduj_wydanie.py rano /tmp/grzyb_dane.json   # albo: wieczor
```

Skrypt dokłada nagłówek wydania, pogodę, obrazy, metryki i **kontrole jakości**
(kategorie, liczby artykułów i akapitów, świeżość źródeł, poprawność linków,
kompletność Literatury), a wynik zapisuje do `/tmp/grzyb_times.html` oraz nazwę pliku
do `/tmp/grzyb_filename`.

**Przeczytaj wypisane logi.** Wpis `error` oznacza realny błąd redakcji (zła kategoria,
link do strony głównej, źródło spoza listy) — **popraw dane i uruchom skrypt ponownie**,
zamiast publikować wydanie z błędem. `warning` przemyśl; `info` zostaw.

## KROK 4 — Publikacja

```bash
cd "$REPO"
git config user.email "grzyb-times@auto.bot"
git config user.name "Grzyb Times Bot"
mkdir -p wydania

# 1) Skopiuj wygenerowane wydanie (nazwa z KROK 3 — spójny czas).
FN=$(cat /tmp/grzyb_filename)
cp /tmp/grzyb_times.html "wydania/$FN"

# 2) Przebuduj archiwum TERAZ, gdy plik już jest w wydania/.
python3 routine/buduj_index.py

# 3) BEZPIECZNIK: nie publikuj, jeśli archiwum nie linkuje nowego wydania.
grep -q "$FN" index.html || { echo "STOP: index.html nie linkuje $FN — przerywam publikację."; exit 1; }

# 4) Commit + push (wydania/ obejmuje też pobrane obrazy wydania/img/…).
git add wydania index.html
git commit -m "Grzyb Times — ${FN%.html}"
git pull --rebase origin main   # do repo pushują też inne rutyny
git push origin main
echo "Opublikowano: https://kapitanski-dev.github.io/wydania/$FN"
```

Na koniec podaj użytkownikowi link do opublikowanego wydania i jedno zdanie
o najważniejszej wiadomości dnia.
