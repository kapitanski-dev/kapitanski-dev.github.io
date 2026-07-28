# Raport finansowy — zapis, budowanie, publikacja

Instrukcja dla rutyny „Przegląd rynku i portfela". **Treść i analiza są w prompcie
rutyny** (tam mieszka kontekst portfela) — tutaj jest wyłącznie to, jak gotowy
raport zapisać, zbudować i opublikować. Przeczytaj ten plik **zanim zaczniesz
pisać raport**: sekcja „Markdown, który renderuje szablon" ogranicza to, czego
możesz użyć.

---

## KROK 1 — Zapisz raport jako markdown

Plik: `raport-finansowy/RRRR-MM-DD-przeglad-rynku.md` (bieżąca data z `date`).
Jeśli plik na dziś już istnieje → sufiks `-2`, `-3`, … Nazwa steruje kolejnością
w archiwum i nawigacją poprzedni/następny, więc **data zawsze z przodu**.

Wymagany front matter — z niego budowana jest strona:

```markdown
---
title: "Przegląd rynku – 28 lipca 2026"
date: 2026-07-28
---
```

- `title` — z niego powstaje nagłówek strony. Człon przed myślnikiem trafia do
  wielkiego H1 (`Przegląd rynku`), dopisek w nawiasie do nadtytułu
  (`(wydanie wieczorne)` → kicker), datę pokazuje pasek pod nagłówkiem.
  Nie kombinuj z formatem — trzymaj wzór `"Przegląd rynku – D miesiąca RRRR"`.
- `date` — `RRRR-MM-DD`, ta sama data co w nazwie pliku.
- **Nie dodawaj `layout:`** — repo nie używa Jekylla (jest `.nojekyll`).

Pierwszy nagłówek `# …` w treści jest przy budowaniu **wycinany** (dublowałby
nagłówek strony), więc możesz go zostawić dla czytelności pliku `.md`.

Struktura treści (jak dotąd): cytat blokowy `>` z kontekstem, `---`, sekcje `##`
(1. Co się stało — TLDR, 2. Portfel pozycja po pozycji, 3. Stan twardych
sygnałów, 4. Werdykt + co dalej obserwować), na końcu `## Źródła` z linkami.
Sekcji `##` powinno być co najmniej 3 — strona buduje z nich spis treści.

## KROK 2 — Markdown, który renderuje szablon

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

## KROK 3 — Zbuduj stronę raportu i archiwum

```bash
cd "$REPO"
python3 routine/buduj_raporty.py    # raport-finansowy/*.md → *.html po raport-template.html
python3 routine/buduj_index.py      # strona główna: sekcja „Raporty finansowe"
```

`buduj_raporty.py` przelicza też nawigację poprzedni/następny we **wszystkich**
raportach, dlatego uruchamiaj go bez argumentów. Nie edytuj `.html` ręcznie —
jedynym źródłem jest `.md` plus `raport-template.html`.

## KROK 4 — Bezpiecznik i publikacja

```bash
cd "$REPO"
FN="raport-finansowy/RRRR-MM-DD-przeglad-rynku"   # bez rozszerzenia, Twoja nazwa z KROK 1

# 1) Strona raportu musi istnieć i nie może zostać z niepodstawionym miejscem na dane.
test -f "$FN.html" || { echo "STOP: brak $FN.html — KROK 3 nie zadziałał."; exit 1; }
grep -q '__TRESC__' "$FN.html" && { echo "STOP: szablon niepodstawiony."; exit 1; }

# 2) Archiwum musi linkować nowy raport.
grep -q "$(basename "$FN").html" index.html || { echo "STOP: index.html nie linkuje raportu."; exit 1; }

# 3) Do repo pushują też rutyny gazety — najpierw pull, potem push.
git config user.email "grzyb-times@auto.bot"
git config user.name "Grzyb Times Bot"
git add raport-finansowy index.html
git commit -m "Raport rynkowy RRRR-MM-DD — <jednozdaniowy werdykt>"
git pull --rebase
git push
```

Commitujesz **oba** pliki raportu: `.md` (źródło) i `.html` (strona). Na koniec
podaj w wiadomości krótkie podsumowanie werdyktu i adres:
`https://kapitanski-dev.github.io/raport-finansowy/RRRR-MM-DD-przeglad-rynku.html`
