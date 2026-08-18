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

## KROK 0.5 — Zgłoszenia (GitHub Issues)

Do repo trafiają dwa rodzaje zgłoszeń: uwagi czytelników (przycisk „Zgłoś uwagę”
przy artykule, tytuł `[Uwaga] …`) i usterki techniczne wykryte przez nocną kontrolę
(`[Auto] …`). Pobierz jedne i drugie — jedno tanie wywołanie, publiczne API bez tokena:

```bash
curl -s "https://api.github.com/repos/kapitanski-dev/kapitanski-dev.github.io/issues?state=open&per_page=20" \
 | python3 -c "import json,sys; [print('-', i['title'], '::', (i.get('body') or '')[:500].replace(chr(10),' ')) for i in json.load(sys.stdin) if i['title'].startswith(('[Uwaga]','[Auto]'))]"
```

**`[Uwaga]` — uwagi czytelników.** Uwzględnij zasadne (błąd merytoryczny, prośba
o temat lub doprecyzowanie) w bieżącym wydaniu i zaloguj każdą:
`{"poziom": "info", "wiadomosc": "Uwaga czytelnika uwzględniona: <tytuł> — <co zrobiono>"}`.
Uwagę bezzasadną lub nie na teraz pomiń bez logowania. **Nie odpowiadaj i nie zamykaj** —
to robi użytkownik.

**`[Auto]` — usterki od automatu**, najczęściej martwe linki źródeł (404). Nie
naprawisz starego wydania i nie masz tego robić, ale **weź to pod uwagę przy
dzisiejszym doborze źródeł**: serwis, który regularnie wraca w tych zgłoszeniach,
przestał być wiarygodny — sięgaj po niego ostrożniej albo wcale. Tych zgłoszeń też
nie zamykaj: zamyka je sam automat, gdy problem zniknie.

Brak zgłoszeń = idź dalej, nic nie loguj.

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
- **Okno obowiązuje KAŻDĄ kategorię.** Nie ma tematów „ponadczasowych”: odkrycie,
  rekord i ciekawostka też mają datę publikacji (wpadka 22.07: rekin goblin sprzed
  14 dni i „pszczoły potu” z kwietnia).
- **`okno_min_h` w kategorii poszerza okno tylko dla niej.** Nauka i Ciekawostka mają
  72 h: recenzowane badanie z przedwczoraj jest tak samo świeże jak wczorajsze, a
  serwisy naukowe publikują nierówno (audyt 30.07: „Nauka” złożona 1/2, bo kandydat
  z Nature Astronomy z 28.07 wypadł poza okno 26 h). To NIE zgoda na tematy sprzed
  tygodnia — 72 h to twardy sufit, a deduplikacja względem naszych wydań obowiązuje
  jak wszędzie. Sprawdź `okno_min_h` w `config.yaml`, nie zgaduj.
- Gdy w kategorii nie ma nic w oknie — daj mniej artykułów. Nie łataj luki starym tematem.
  Zanim jednak zejdziesz poniżej `liczba`, **przejdź całą listę źródeł kategorii**:
  Nauka to nie tylko sciencedaily.com i phys.org, ale też eurekalert.org (komunikaty
  wprost od czasopism — największy dzienny wolumen), naukawpolsce.pl (polskie badania),
  sciencenews.org, sciencealert.com i livescience.com. Luka po jednym zapytaniu to
  najczęściej za wąski research, nie brak materiału na świecie.
- **Software Development AI** ma cztery obszary i osobne źródła do każdego — jedno
  zapytanie ich nie obsłuży. Narzędzia AI dla programistów: github.blog (changelog
  Copilota), anthropic.com, devblogs.microsoft.com. Java i Spring: spring.io,
  inside.java, infoq.com. Architektura i praktyki: martinfowler.com, infoq.com.
  Trzymaj obszary w rotacji między wydaniami — dwa artykuły dziennie z tego samego
  obszaru przez tydzień to nie jest przegląd branży.
- **Tego dnia** nie ma okna świeżości (pomiń `zrodlo.opublikowano` — to rocznica, nie
  news) i nie idzie przez WebSearch, tylko przez dwie strony Wikipedii dla dzisiejszej
  daty: `https://pl.wikipedia.org/wiki/D_miesiąc` (np. `3_sierpnia`) i
  `https://en.wikipedia.org/wiki/Month_D` (np. `August_3`) — obie mają sekcję
  „Wydarzenia”/„Events” z listą rocznic. Otwórz obie (WebFetch), **zweryfikuj datę
  w treści strony, nie pisz z pamięci** (poeci są z pamięci, historia — nie: fakty
  i daty łatwo pomylić). Kolejność wyboru z `config.yaml`: najpierw wydarzenie
  światowe o realnym znaczeniu, potem — gdy światowego brak — wydarzenie polskie
  przed innymi krajami. `zrodlo.url` to strona dnia, na której znalazłeś wydarzenie
  (polski wątek → pl.wikipedia.org, światowy → en.wikipedia.org); `zrodlo.nazwa`:
  `"Wikipedia"`. Dwa artykuły w kategorii nie mogą opisywać tego samego wydarzenia
  ani wracać do tego, co już było w tej kategorii w poprzednich wydaniach (zwykła
  deduplikacja wyżej — data w roku się powtarza, więc pilnuj tego świadomie przy
  dwóch wydaniach tego samego dnia).
- Skrypt raportuje wiek źródeł **zbiorczo**; nie loguj tego ręcznie.

### Wyjątek od okna: NADROBIENIE przegapionego newsa (OBOWIĄZKOWY)

Okno świeżości jest twarde w jedną stronę — nie wpuszcza starych tematów jako
„newsa dnia”. Ale samo w sobie nie odróżnia tematu nieistotnego od tematu, który
**był ważny i któremu daliśmy się przespać**. Bez tego wyjątku pominięcie
kasuje news na zawsze: wczoraj był poza researchem, dziś jest poza oknem.

**Zasada: news, którego waga uzasadniałaby okładkę, wchodzi do wydania nawet po
przekroczeniu okna — jeśli nie było go w ŻADNYM z naszych trzech ostatnich wydań.**
Warunki, wszystkie naraz:

- temat wygrałby dziś kryterium „realny skutek” z sekcji *Jak wybierać* (ofiary
  śmiertelne, katastrofa, atak, decyzja o dużym skutku) — a nie jest po prostu
  ciekawy;
- nie ma go w żadnym z trzech ostatnich plików w `wydania/` (te sprawdzasz i tak
  przy deduplikacji);
- piszesz go od **aktualnego stanu sprawy**, nie od zdarzenia: bilans po dwóch
  dniach, ustalenia śledztwa, reakcje, skutki. Nadrobienie to nie przedruk
  wczorajszej depeszy.

Ustaw wtedy `"kontynuacja": true` i **zaloguj to wprost**:
`{"poziom": "warning", "wiadomosc": "Nadrobienie: <tytuł> (zdarzenie <data>) — pominięte w wydaniach <lista>, wchodzi mimo okna <N> h."}`
Log jest obowiązkowy: to sygnał do audytu, że research poprzedniego wydania miał dziurę.

Wpadka, której to zapobiega (16–18.08.2026): w nocy z 15 na 16.08 autokar z 59
polskimi pielgrzymami dachował na węgierskiej autostradzie M3 — **12 zabitych,
10 ciężko rannych, wszyscy z Podkarpacia**. Wydanie z 16.08 (4:35) powstało
zanim news się rozszedł, ale wydanie z **17.08 nie miało o tym ani słowa**,
mimo że temat był w sieci od doby i to w źródłach z naszej listy (Euronews,
Al Jazeera, Interia). Wpadł dopiero na okładkę 18.08 — **dwa dni po zdarzeniu**,
z datą źródła poza oknem. Czytelnik dostał największą polską tragedię tygodnia
jako „news dnia” wtedy, gdy w kraju trwała już żałoba.

### Jedno źródło nie niesie kategorii (OBOWIĄZKOWE)

Audyt 04.08.2026 pokazał monokulturę: **Al Jazeera dała 77% kategorii Wojna** (40 z 52
artykułów) i **75% okładek**, a sciencedaily.com — 87% Nauki. Czytelnik dostawał wtedy
jedną redakcję i jedną perspektywę, podpisaną jako przegląd świata.

**Zasada: żadna kategoria nie może w całości pochodzić z jednego serwisu.** Przy
`liczba: 3` weź materiał z co najmniej dwóch różnych domen; przy `liczba: 2` staraj się
o dwie, ale jedna jest dopuszczalna, gdy temat naprawdę jest tylko tam. Skrypt liczy to
sam i loguje `warning` przy 3/3 z jednej domeny oraz gdy jedna domena przekroczy 40%
całego wydania (mediana archiwum to 29%).

Praktycznie — **Wojna** ma teraz źródła w czterech grupach, nie w jednej. Jedno
zapytanie ich nie obsłuży, więc rozłóż sloty:

- **Ukraina i Rosja:** kyivindependent.com (publikuje 24/7, dobre na nocny ostrzał),
  ukrinform.net;
- **Bliski Wschód:** aljazeera.com, amwaj.media, middleeasteye.net — to nadal mocna
  grupa, ale ma być JEDNĄ z czterech, nie całą kategorią;
- **Obronność i wojskowość:** defensenews.com, militarytimes.com, breakingdefense.com —
  sprzęt, kontrakty, decyzje zbrojeniowe;
- **Polski trop:** defence24.pl i konflikty.pl (po polsku), notesfrompoland.com (po
  angielsku). Gazetę czyta Polak, a kategoria do 04.08.2026 nie miała ANI JEDNEGO
  polskiego źródła — sprawdzaj tu wątek polski, zwłaszcza NATO i granicę.

Generaliści (bbc.com, dw.com, euronews.com, npr.org) nadają się i do Wojny, i do
Okładki, i do Polityki — sięgaj po nich, gdy okładka robi się co dzień z tego samego
serwisu. Think tanki (understandingwar.org, warontherocks.com, csis.org,
atlanticcouncil.org) to **analiza i komentarz, nie doniesienie**: dobre na tło
i kontekst, ale news dnia ma stać na źródle faktograficznym.

Ta sama zasada dotyczy kategorii, które wyglądają niewinnie: **Nauka** ma sześć źródeł
(eurekalert.org, sciencedaily.com, phys.org, sciencenews.org, sciencealert.com,
naukawpolsce.pl), a wychodziła prawie w całości z jednego. Jeśli oba artykuły Nauki
biorą się z tego samego serwisu w kolejnych wydaniach, research kończy się na pierwszym
trafieniu — zejdź niżej na liście.

### Przegląd nocy, polski trop i luki (OBOWIĄZKOWY, przed kategoriami)

Wydanie poranne powstaje po 8:00 rano (rutyna startuje o 6:00 UTC — przesunięta z 3:00
UTC po wpadce opisanej niżej, a realny cron rutyny doprowadzono do tej wartości dopiero
18.08.2026: przez trzy tygodnie chodził wciąż o 2:00 UTC, czyli 4:00 rano czasu polskiego,
i stąd „noc nieodrobiona” w logach niemal każdego wydania z sierpnia), więc **noc jest
jego najważniejszym materiałem** — i jednocześnie najłatwiejszym do przespania: polskie
serwisy publikują nocne wydarzenia dopiero od ~7:00, a WebSearch indeksuje świeże newsy
z opóźnieniem. Zanim zaczniesz wypełniać kategorie, zadaj trzy pytania wprost:

1. **Co wydarzyło się w nocy?** Ostrzały, ataki, incydenty, decyzje z innych strefy
   czasowych. Pytaj o dzisiejszą datę wprost („mass attack Ukraine 30 July”, „overnight
   strikes”), nie o „najnowsze wiadomości”. Nocne wydarzenie należy do wydania nawet
   jeśli szczegóły są jeszcze niepełne — wtedy pisz to, co potwierdzone, a niewiadome
   nazwij niewiadomymi.
2. **Czy cokolwiek dotyka POLSKI albo POLAKÓW?** Gazetę czyta Polak: sprawa polska
   bije wagą podobny news z drugiego końca świata i **zasługuje na okładkę**. Dwa
   równorzędne tropy, obydwa sprawdź osobnym zapytaniem — nie licz na to, że wypadną
   z researchu kategorii:
   - **Polska jako terytorium i państwo:** przestrzeń powietrzna, NATO, granica, wojsko,
     infrastruktura krytyczna, ewakuacje, decyzje rządu.
   - **Polacy jako ludzie:** katastrofy i wypadki masowe z polskimi ofiarami — w kraju
     **i za granicą** (autokary, samoloty, promy, pożary, zawalenia), zaginięcia
     i śmierć Polaków w wypadkach zbiorowych, żałoba narodowa, akcje ratunkowe
     i ewakuacje obywateli. Ten trop nie ma nic wspólnego z bezpieczeństwem państwa
     i **przez to bywał pomijany** (wpadka 16–18.08.2026, opisana wyżej przy nadrabianiu):
     12 Polaków zginęło w wypadku autokaru na Węgrzech, a gazeta milczała przez dwa dni.
     Zapytania po polsku i po angielsku („Polacy zginęli”, „Polish tourists killed”,
     „Polish nationals crash”) — bo pierwsze podaje to serwis kraju zdarzenia, nie polski.
3. **Czego zabrakło w poprzednich wydaniach?** Zadaj jedno szerokie pytanie o
   najważniejsze wydarzenia ostatnich 48 h — osobno o świat i osobno o Polskę — i zestaw
   odpowiedź z tematami trzech ostatnich plików z `wydania/` (i tak je czytasz przy
   deduplikacji). Duży news, którego u nas nie ma, **nie jest przeterminowany, tylko
   przespany** — wchodzi trybem NADROBIENIA (sekcja wyżej), z logiem `warning`.

**Gdy polskie serwisy jeszcze milczą, weź źródła obcojęzyczne z listy** (aljazeera.com
działa 24/7) — to one pierwsze podają nocne wydarzenia z Europy Wschodniej, często
z polskim wątkiem w środku tekstu („Poland scrambled fighter jets”).

Wpadka, której to zapobiega (30.07.2026): w nocy Rosja wystrzeliła w Ukrainę 70+ rakiet
i ~280 dronów, o 3:40 obiekt wleciał w polską przestrzeń powietrzną i spadł pod
Tarnawą-Kolonią (10-metrowy lej, 70 km od granicy, F-16 w powietrzu). Wydanie z 5:29
nie miało o tym ani słowa — trzy miejsca w kategorii Wojna zajęły tematy z 29.07,
a nocny atak opisywała Al Jazeera, czyli źródło z naszej listy. Sam polski krater
wypłynął na pap.pl i bankier.pl dopiero o 7:20–7:29 — dwie godziny PO publikacji, więc
jego złapać nie było jak (stąd przesunięcie rutyny na 8:00), ale nocnego ostrzału
Ukrainy z polskim wątkiem owszem.

Skrypt to kontroluje: wydanie, w którym **mniej niż 2 artykuły mają datę źródła z dnia
publikacji**, dostaje `warning` „noc/poranek wygląda na nieodrobiony”.

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

**Okładka ma być świeża.** Jej `zrodlo.opublikowano` nie może być starsze niż okno
świeżości — jedyny wyjątek to NADROBIENIE (sekcja wyżej), i wtedy okładka wymaga loga
`warning` z tej sekcji. Okładka z datą sprzed dwóch dni bez takiego loga to błąd
redakcji, nie decyzja: czytelnik odbiera ją jako „gazeta nie wie, co się dzieje”
(wpadka 18.08.2026 — wypadek autokaru na Węgrzech z 16.08 na okładce dwa dni później).

**Trzy ostatnie okładki są listą zakazaną co do WĄTKU, nie tylko co do newsa.** Cztery
poranki z rzędu z tego samego konfliktu to nie jest „news numer jeden”, tylko brak
przeglądu — chyba że wątek realnie eskalował i to widać w faktach z ostatniej doby.

### Deduplikacja względem poprzedniego wydania (OBOWIĄZKOWA)

Zanim zaczniesz research, przeczytaj **TRZY najnowsze pliki** z `"$REPO/wydania/"`
(sortowanie po nazwie) i wynotuj ich tematy — tytuły i kategorie z JSON-a w
`<script id="dane-gazety">`. To czytanie lokalne, nie kosztuje tokenów sieci.
Najnowszy plik służy deduplikacji, a wszystkie trzy — pytaniu „czego zabrakło?”
z przeglądu nocy: bez nich nie odróżnisz newsa już opisanego od przespanego.

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
z omówieniem na JEDEN akapit.

### Dwie żelazne zasady tej rubryki

**1. ZERO związku z newsami — to ma być świeże spojrzenie.** Czytelnik przechodzi tu
po dwudziestu artykułach o wojnie i stopach procentowych; rubryka jest oddechem, nie
kolejnym komentarzem do wydania. Omówienie mówi o **samym tekście**: co znaczy, na
jakim obrazie stoi, skąd się wzięło, dlaczego warto na nim zatrzymać wzrok, jak brzmi
w uchu. **Nie wolno** nawiązywać do artykułów tego wydania — ani wprost („jak
w dzisiejszym artykule”, „w kontekście wydarzeń dnia”), ani przez nazwy z newsów
(Iran, Fed, Meta, Ukraina). Skrypt to sprawdza: nazwa własna z tytułu artykułu albo
zwrot odsyłający do wydania = `warning` w Logs. (Feedback czytelnika 30.07: „opisy
są dalej powiązane z artykułami, a to powinno być świeże spojrzenie”. Wcześniejsza
wersja instrukcji dopuszczała takie powiązanie — już nie.)

**2. ZERO powtórek.** Rutyna startuje bez pamięci poprzednich przebiegów, więc bez
sprawdzenia archiwum wracasz do tych samych, najoczywistszych pozycji (audyt 30.07:
Kochanowski w 5 wierszach z 6, „Na zdrowie” i „Kuj żelazo, póki gorące” po dwa razy
w trzy dni, `resilience` dwa razy w trzy dni). **Zanim zaczniesz składać rubrykę,
wypisz listę zajętą:**

```bash
python3 routine/literatura_historia.py     # okno z config.yaml (30 wydań)
```

Zasady na podstawie tej listy: **wiersz, przysłowie, cytat, słowo i zwrot** nie mogą
się powtórzyć w całym oknie, a **autor wiersza i autor cytatu** — w 10 ostatnich
wydaniach. Skrypt budujący wydanie sprawdza to jeszcze raz i loguje każdą powtórkę
jako `warning`, więc obejście „nikt nie zauważy” nie istnieje. Świat jest ogromny:
setki poetów, tysiące przysłów — jeśli sięgasz po Kochanowskiego trzeci raz w tygodniu,
problem jest w Twoim doborze, nie w zasobie.

1. **Cytat dnia** — myśl znanego autora. Podaj `autor` i (jeśli znasz) `zrodlo` (dzieło)
   albo `"przypisywane"`, gdy atrybucja niepewna. Cytuj wiernie; nie zmyślaj autorstwa.
   Wyjdź poza żelazną piątkę mądrości motywacyjnych (Churchill, Einstein, Buffett):
   filozofia, literatura, nauka, sztuka, myśl spoza Europy — cytat ma zaskakiwać.
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
   zmarły ponad 70 lat temu. ZAKAZ: Miłosz (†2004), Szymborska (†2012), Herbert (†1998),
   Staff (†1957), Lechoń (†1956).

   **Rotuj autorów i epoki** — wiersz z każdego wydania ma pochodzić od kogoś innego niż
   dziesięć poprzednich (kontrola w skrypcie). Bezpieczna pula jest szeroka, korzystaj
   z całej: renesans i barok (Kochanowski, Rej, Sęp-Szarzyński, J.A. Morsztyn, Naruszewicz),
   oświecenie (Krasicki, Trembecki, Karpiński), romantyzm (Mickiewicz, Słowacki, Norwid,
   Krasiński, Fredro), pozytywizm i Młoda Polska (Konopnicka, Asnyk, Kasprowicz, Przerwa-Tetmajer,
   Wyspiański), dwudziestolecie (Leśmian, Tuwim †1953, Gałczyński †1953,
   Pawlikowska-Jasnorzewska †1945, Baczyński †1944). Poeci obcy też są w puli (Horacy,
   Katullus, Szekspir, Blake, Dickinson, Heine, Baudelaire, Verlaine, Rilke †1926, Bashō) —
   ale ich **przekład** też musi być w domenie publicznej: albo klasyczny stary przekład,
   albo podaj oryginał i własne, dosłowne tłumaczenie w omówieniu.

   **ŻELAZNA zasada nr 2: wiersz obcojęzyczny (angielski i każdy inny) MUSI mieć polskie
   tłumaczenie.** Jeśli `tresc` zostaje w oryginale (bo nie znasz klasycznego przekładu),
   `omowienie` MA zawierać tłumaczenie tekstu na polski — czytelnik nie może dostać
   wersu, którego nie rozumie, bez żadnego wyjaśnienia po polsku obok. Sam „komentarz
   o utworze” bez samego tłumaczenia to za mało. Skrypt to sprawdza (heurystyka: brak
   polskich znaków diakrytycznych w `tresc` + brak śladu tłumaczenia w `omowienie` =
   `warning`), ale nie polegaj na tym — dopilnuj tego przy składaniu rubryki.
4. **Angielski na dziś** — jedno przydatne `slowo` (z `wymowa` w IPA, `znaczenie` po polsku,
   `przyklad` w formacie `"zdanie EN — tłumaczenie PL"`) oraz jeden idiomatyczny `zwrot`
   (`zwrot_znaczenie`, `zwrot_przyklad` w tym samym formacie). Poziom średnio-zaawansowany,
   słownictwo przydatne przy czytaniu prasy — ale **nie ciągle to samo poletko**: `resilience`,
   `volatile`, `deterrence`, `leverage` i `to weather the storm` już były (patrz lista zajęta).
   Zdanie przykładowe nie musi być z gazety; codzienna sytuacja jest równie dobra.

Cała sekcja powstaje z **własnej wiedzy** — nie zależy od sieci, więc ma być KOMPLETNA
(4/4) w każdym wydaniu; skrypt ostrzega przy brakach.

Poniższy JSON pokazuje **wyłącznie strukturę pól** — treści są celowo puste, żeby nie
wracały do wydań. (Wpadka 25–27.07: `resilience` i `to weather the storm` z dawnego
przykładu trafiły wprost do dwóch wydań.)

```json
{
  "cytat": {"tresc": "<cytat>", "autor": "<autor>", "zrodlo": "<dzieło albo „przypisywane”>", "omowienie": "Jeden akapit o samej myśli — bez odniesień do newsów."},
  "przyslowie": {"tresc": "<przysłowie polskie>", "pochodzenie": "przysłowie polskie", "odpowiedniki": [{"jezyk": "ang.", "tresc": "<wersja angielska>", "tlum": "<dosłowne tłumaczenie>"}, {"jezyk": "łac.", "tresc": "<wersja łacińska>", "tlum": "<dosłowne tłumaczenie>"}, {"jezyk": "jp", "tresc": "<zapis japoński (transkrypcja)>", "tlum": "<dosłowne tłumaczenie>"}], "omowienie": "Jeden akapit o sensie przysłowia."},
  "wiersz": {"tytul": "<tytuł>", "autor": "<autor z domeny publicznej>", "tresc": "<cały wiersz,\nwers po wersie>", "omowienie": "Jeden akapit o tekście: obraz, forma, kontekst powstania."},
  "angielski": {"slowo": "<słowo>", "wymowa": "<IPA>", "znaczenie": "<po polsku>", "przyklad": "<zdanie EN> — <tłumaczenie PL>", "zwrot": "<idiom>", "zwrot_znaczenie": "<po polsku>", "zwrot_przyklad": "<zdanie EN> — <tłumaczenie PL>"}
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
kompletność Literatury, powtórki i doklejenia w Literaturze), a wynik zapisuje
do `/tmp/grzyb_times.html` oraz nazwę pliku do `/tmp/grzyb_filename`.

**Przeczytaj wypisane logi.** Wpis `error` oznacza realny błąd redakcji (zła kategoria,
link do strony głównej, źródło spoza listy) — **popraw dane i uruchom skrypt ponownie**,
zamiast publikować wydanie z błędem. `warning` przemyśl; `info` zostaw.

Dwa `warningi` traktuj jak `error`, bo obie rzeczy naprawiasz w minutę bez researchu:
**powtórkę w Literaturze** (podmień pozycję na taką, której nie ma na liście zajętej)
i **Literaturę wracającą do newsów** (przepisz omówienie tak, by mówiło o samym tekście).

## KROK 4 — Publikacja

**WAŻNE:** publikuj WYŁĄCZNIE na branch `main`. **Nigdy** nie twórz nowego brancha,
nie otwieraj Pull Requesta i nie używaj `gh pr create`. Jeśli push nie przejdzie za
pierwszym razem — ponów (pętla niżej), nie przełączaj się na branch. Do `main` pushują
równolegle workflow grafik i inne rutyny, więc wyścig jest normalny i retry go rozwiązuje.

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

# 4) Commit + push z retry (do main pushują też inne rutyny — wyścig jest normalny).
git add wydania index.html dane
git commit -m "Grzyb Times — ${FN%.html}"
for i in 1 2 3; do
  git pull --rebase origin main && git push origin main && break
  echo "Push nieudany (próba $i) — ponawiam za 5 s."
  sleep 5
done
echo "Opublikowano: https://kapitanski-dev.github.io/wydania/$FN"
```

Na koniec podaj użytkownikowi link do opublikowanego wydania i jedno zdanie
o najważniejszej wiadomości dnia.
