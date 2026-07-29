# Raport finansowy — research, zapis, publikacja

Instrukcja dla rutyny „Przegląd rynku i portfela”. **Kontekst portfela i teza
inwestycyjna są w prompcie rutyny** (repo jest publiczne) — tutaj jest to, co
powtarzalne: skąd brać dane, jak raport zapisać, zbudować i opublikować.
Przeczytaj ten plik **zanim zaczniesz pisać** — sekcja „Markdown, który renderuje
szablon” ogranicza to, czego możesz użyć.

---

## KROK 0 — Ciągłość: co obiecał poprzedni raport

Zanim zaczniesz research, przeczytaj **najnowszy** plik `.md` z `raport-finansowy/`
(sortowanie po nazwie; `.html` to zbudowane strony — nie czytaj ich i nie edytuj).
Wynotuj dwie rzeczy:

1. **Werdykt i tezy** — żeby dzisiejszy raport był kolejnym odcinkiem, a nie
   powtórką od zera.
2. **Listę z sekcji „Co obserwować”** — to zapowiedzi, które sami złożyliśmy
   czytelnikowi (wyniki spółek, decyzje banków centralnych, starty, głosowania).
   Dla KAŻDEJ pozycji sprawdź w researchu, czy się rozstrzygnęła:
   - **rozstrzygnęła się** → opisz wynik w raporcie (to priorytet — obiecaliśmy ciąg dalszy);
   - **wciąż otwarta** → przenieś do „Co obserwować” w nowym raporcie;
   - **straciła aktualność** → porzuć.

Raport zaczynaj od sekcji **„Co nowego od poprzedniego raportu (<data>)”** — kilka
punktów o tym, co realnie się zmieniło od ostatniego przeglądu.

## KROK 1 — Skąd brać dane

Raport ma być weryfikowalny, więc źródła dobieraj w tej kolejności:

1. **Pierwotne** — komunikaty wynikowe i relacje inwestorskie spółek, raporty
   bieżące, komunikaty banków centralnych i urzędów statystycznych, dane giełdowe.
2. **Poważna prasa finansowa** — Bloomberg, Financial Times, Yahoo Finance, CNBC,
   Bankier, money.pl, Puls Biznesu, Stooq (notowania).
3. **Reszta** — tylko gdy potwierdza to, co już masz z (1) lub (2).

**Nie linkuj farm treści i agregatorów SEO** (audyt 28.07: w Źródłach wylądowały
tradingkey.com, menafn.com, indexbox.io, foreignpolicyjournal.com). Jeśli temat
istnieje wyłącznie tam — traktuj go jako plotkę i tak go opisz.

Zasady liczb:

- **Kurs USD/PLN pobierz raz** i użyj spójnie w całym raporcie; podaj go pod
  nagłówkiem („Kurs USD/PLN w dniu raportu: ok. **3,80 zł**”).
- **Nie zgaduj notowań.** Nie masz pewnego kursu zamknięcia? Napisz, czego nie
  udało się potwierdzić, zamiast wpisywać liczbę „mniej więcej”.
- Każdą kwotę w USD/EUR podaj z przybliżeniem w złotych: „250 mld USD (~950 mld zł)”.
- Adresy w sekcji Źródła kopiuj **1:1 z wyników wyszukiwania** — nie składaj ich
  z wzorca domeny.

## KROK 2 — Zapisz raport jako markdown

Plik: `raport-finansowy/RRRR-MM-DD-przeglad-rynku.md` (bieżąca data z `date`).
Jeśli plik na dziś już istnieje → sufiks `-2`, `-3`, … Nazwa steruje kolejnością
w archiwum i nawigacją poprzedni/następny, więc **data zawsze z przodu**.

Wymagany front matter — z niego budowana jest strona (inne klucze są ignorowane,
`layout:` nie jest potrzebny, bo repo nie używa Jekylla):

```markdown
---
title: "Przegląd rynku – 28 lipca 2026"
date: 2026-07-28
---
```

- `title` — człon przed myślnikiem trafia do wielkiego H1 (`Przegląd rynku`),
  dopisek w nawiasie do nadtytułu (`(wydanie wieczorne)` → kicker), datę pokazuje
  pasek pod nagłówkiem. Trzymaj wzór `"Przegląd rynku – D miesiąca RRRR"`.
- `date` — `RRRR-MM-DD`, ta sama data co w nazwie pliku.

Pierwszy nagłówek `# …` w treści jest przy budowaniu **wycinany** (dublowałby
nagłówek strony), więc możesz go zostawić dla czytelności pliku `.md`.

### Struktura treści

Cytat blokowy `>` z kontekstem, `---`, a dalej sekcje `##` (spis treści strony
buduje się z nich, więc ma być co najmniej 3):

1. **Co nowego od poprzedniego raportu (<data>)** — patrz KROK 0.
2. **Co się stało — TLDR** — jedno zdanie werdyktu, potem 2–3 najważniejsze wątki.
3. **Portfel — pozycja po pozycji** — tabela; przy każdej pozycji rozróżnij ruch
   „razem z rynkiem” od powodu fundamentalnego.
4. **Stan twardych sygnałów** — wprost, sygnał po sygnale: zapalił się czy nie.
5. **Werdykt + co dalej obserwować** — szum / okazja / sygnał ostrzegawczy,
   z dowodami ZA i PRZECIW (nie uspokajaj na siłę, ale też nie strasz nagłówkami).
6. **Źródła** — lista `- [tytuł — serwis](url)`.

Sekcja 5 musi kończyć się podsekcją **`### Co obserwować`** — to wejście dla
następnego raportu (KROK 0), więc nagłówek nazywaj dokładnie tak, a każda pozycja
ma mieć **termin** i **dlaczego to ważne**. Tabela (`Termin | Co czekamy | Dlaczego
ważne`) sprawdza się tu równie dobrze jak lista punktowa:

```markdown
- **30.07 (czwartek)** — wyniki Amazona za Q2: wzrost AWS i utrzymanie capexu.
- **do końca sierpnia** — wyniki NVIDIA: czy zamówienia spadły po Kimi K3.
```

Język: po polsku, prosto — czytelnik nie jest finansistą. Bez żargonu, a jeśli
termin jest konieczny, wyjaśnij go po ludzku w tym samym zdaniu. Raport trafia na
publiczną stronę, więc pisz jak do publikacji.

## KROK 3 — Markdown, który renderuje szablon

Konwerter (`routine/buduj_raporty.py`) jest mały i bez zależności. **Obsługuje:**

| Konstrukcja | Zapis |
|---|---|
| Nagłówki | `## Sekcja`, `### Podsekcja` (H1 tylko pierwszy, wycinany) |
| Akapity | zwykły tekst, pusta linia rozdziela |
| Wyróżnienia | `**pogrubienie**`, `*kursywa*`, `` `kod` `` |
| Odnośniki | `[tekst](https://…)` |
| Listy | `- punkt` oraz `1. punkt` |
| Cytat | `> tekst` |
| Tabela | GFM: wiersz nagłówka + `|---|---|` + wiersze |
| Linia | `---` w osobnej linii |

**Nie używaj** (nie zostanie zrenderowane): bloków kodu ` ``` `, obrazków `![]()`,
surowego HTML, list zagnieżdżonych, przekreślenia `~~`, przypisów, wyrównania
kolumn przez `:---:`. Tabele buduj bez pustych wierszy w środku.

Tabele są sednem raportu i **nigdy nie przewijają się poziomo**: na szerokim
ekranie wychodzą poza kolumnę tekstu, a na wąskim każdy wiersz rozkłada się na
kartę z podpisami kolumn. Dlatego nie bój się 5–6 kolumn. Dwie zasady: nagłówki
kolumn krótkie (stają się podpisami w kartach) i **pierwsza kolumna to nazwa
pozycji** (ETF, spółka, sygnał) — na wąskim ekranie jest tytułem karty.

## KROK 4 — Zbuduj stronę raportu i archiwum

```bash
cd "$REPO"
python3 routine/buduj_raporty.py    # raport-finansowy/*.md → *.html po raport-template.html
python3 routine/buduj_index.py      # strona główna: sekcja „Raporty finansowe”
```

`buduj_raporty.py` uruchamiaj **bez argumentów** — przelicza nawigację
poprzedni/następny we wszystkich raportach, więc zmienia też plik poprzedniego
raportu. Nie edytuj `.html` ręcznie; jedynym źródłem jest `.md` + `raport-template.html`.

## KROK 5 — Bezpieczniki i publikacja

Jeden raport = **jeden commit** (wpadka 29.07: nawigacja poprzedniego raportu
poszła osobnym commitem, bo pliki zostały dodane przed przebudową).

```bash
cd "$REPO"
FN="raport-finansowy/RRRR-MM-DD-przeglad-rynku"   # bez rozszerzenia, Twoja nazwa z KROK 2

# 1) Strona raportu musi istnieć i nie może zostać z niepodstawionym miejscem na dane.
test -f "$FN.html" || { echo "STOP: brak $FN.html — KROK 4 nie zadziałał."; exit 1; }
grep -q '__TRESC__' "$FN.html" && { echo "STOP: szablon niepodstawiony."; exit 1; }

# 2) Archiwum musi linkować nowy raport.
grep -q "$(basename "$FN").html" index.html || { echo "STOP: index.html nie linkuje raportu."; exit 1; }

# 3) Do repo pushują też rutyny gazety — najpierw pull, potem push.
git config user.email "grzyb-times@auto.bot"
git config user.name "Grzyb Times Bot"
git add raport-finansowy index.html
git status --short                  # nic poza raport-finansowy/ i index.html nie powinno zostać
git commit -m "Raport rynkowy RRRR-MM-DD — <jednozdaniowy werdykt>"
git pull --rebase origin main
git push origin main
```

Commitujesz **oba** pliki raportu: `.md` (źródło) i `.html` (strona) oraz
`index.html` i przeliczoną nawigację starszych raportów. Na koniec podaj
w wiadomości krótkie podsumowanie werdyktu (3–5 zdań) i adres:
`https://kapitanski-dev.github.io/raport-finansowy/RRRR-MM-DD-przeglad-rynku.html`
