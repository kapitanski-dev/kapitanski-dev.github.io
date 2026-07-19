# Grzyb Times

Cyfrowa gazeta redagowana przez AI, publikowana **2× dziennie** (rano i wieczorem)
na GitHub Pages: **https://kapitanski-dev.github.io**

Wydania generują dwie chmurowe rutyny Claude Code (cron), które klonują to repo,
czytają z niego konfigurację + szablon + instrukcję, robią research w sieci,
składają wydanie i wypychają je z powrotem do repo.

---

## Struktura repo

| Plik / katalog | Rola |
|---|---|
| `config.yaml` | **Konfiguracja, którą edytujesz Ty.** Kategorie i liczby artykułów, źródła, liczba akapitów, pogoda, tryb researchu wtórnego. |
| `template.html` | Szablon wydania (HTML+CSS+JS). Placeholder `__DANE__` = dane wydania. Otwarty bez danych pokazuje **podgląd Lorem Ipsum** (blok DEMO — rutyna wycina go z wydań). |
| `routine/instrukcja.md` | Pełna instrukcja dla AI: research → redakcja → generacja → publikacja. |
| `routine/czysc_stare.py` | Czyszczenie starych wydań (patrz niżej). |
| `index.html` | Auto-generowane archiwum wydań (strona główna, grupowanie po dniach). |
| `wydania/` | Gotowe wydania `RRRR-MM-DD-{rano\|wieczor}-GGMM.html` + `wydania/img/` (pobrane grafiki artykułów). **Opublikowanych wydań nie edytujemy.** |
| `assets/kategorie/` | Zdjęcia bazowe kategorii (2–3 na kategorię, rotacja przeciw duplikatom). |
| `raport-finansowy/` | Osobna rutyna: cotygodniowe przeglądy rynku (niezależne od gazety). |

**Cała logika jest w repo.** Rutyny to cienki bootstrap („znajdź repo → przeczytaj
`routine/instrukcja.md` → wykonaj"). Zmiana czegokolwiek = commit, bez ruszania rutyn.

---

## Jak to działa

```
cron (7:00 / 19:00) → rutyna klonuje repo → config.yaml + template.html + instrukcja.md
      ↓
uwagi czytelników (GitHub Issues „[Uwaga] …”) + wątki z poprzedniego wydania (follow-upy)
      ↓
research (WebSearch) wg kategorii i źródeł; rubryka ocen: realny skutek > skala > nowość
      ↓
redakcja: 4 akapity, skróty, kwoty z ~PLN, tooltipy {{termin|wyjaśnienie}}, timestampy źródeł
      ↓
skrypt: JSON → template (__DANE__), og:image artykułów do wydania/img/, pogoda z Interii,
        walidacje (kategorie, liczby, akapity) → logi
      ↓
index.html + git commit + push → GitHub Pages
```

### Obrazy (trzy warstwy, wszystkie automatyczne)
1. **og:image artykułu źródłowego** — skrypt pobiera grafikę newsa i commituje do
   `wydania/img/…` (ten sam origin ⇒ ładuje się zawsze; zero tokenów LLM).
2. Fallback: **zdjęcie kategorii** z `assets/kategorie/` (rotacja 2–3 zdjęć).
3. Bonus: przeglądarka czytelnika może podmienić zdjęcie kategorii na trafniejsze
   z Wikimedia Commons (`obraz.query`).

### Funkcje wydania
„W skrócie" (jednozdaniowe streszczenia z kotwicami) · filtry kategorii (start:
Okładka) · badge „Aktualizacja" przy kontynuacjach · interaktywne wykresy (tylko
gdy źródło daje komplet danych) · kluczowe liczby · tooltipy trudnych terminów ·
czas czytania · timestamp publikacji u źródła · „Zgłoś uwagę" (GitHub Issue,
rutyna czyta je przy kolejnym wydaniu) · pogoda z Interii (klik → pełna prognoza) ·
nawigacja poprzednie/następne · sekcja **Logs** (diagnostyka rutyny, w tym model
generujący wydanie) · motyw jasny/ciemny · design „paper & ink" (mobile/tablet/desktop + druk).

---

## Jak zmieniać gazetę

Edytujesz plik → `git commit` + `git push`. Najbliższe wydanie użyje nowej wersji.

### Kategorie — `config.yaml`
```yaml
kategorie:
  - nazwa: Inwestowanie
    liczba: 3               # ile artykułów; suma liczb = wielkość wydania
    zakres: "co obejmuje… (i czego NIE — zakazy pisz wprost)"
    wykres: preferowany     # preferowany | opcjonalny | nie
```
- Kolejność = ważność; pierwsza kategoria (Okładka, `liczba: 1`) = artykuł otwierający.
- Nowa kategoria wymaga zdjęcia: `assets/kategorie/<nazwa>.jpg` (≤1000px JPEG)
  + wpis w mapie `KAT_OBRAZ` w `template.html` (lista = rotacja).

### Źródła — `config.yaml`
Zamknięta lista `zrodla_pierwotne` (link artykułu musi z niej pochodzić).
**Przed dodaniem domeny sprawdź jej `robots.txt`** — jeśli blokuje `Claude-User`,
jest bezużyteczna (tak wypadły reuters.com, apnews.com, cnbc.com, theverge.com).
Research wtórny: `research_wtorny.tryb` = `nigdy | wyjatkowo | swobodnie`.

### Pogoda — `config.yaml`
`pogoda.prognoza_url` (strona Interii dla miasta; skrypt parsuje z niej aktualny
stan, klik w pasek pogody ją otwiera) + `lat`/`lon` (fallback Open-Meteo).

### Wygląd — `template.html` · Proces redakcyjny — `routine/instrukcja.md`

---

## Czyszczenie starych wydań

Repo rośnie ~1 MB na wydanie (grafiki). Gdy chcesz przyciąć:

```bash
python3 routine/czysc_stare.py --dni 60        # usuń wydania starsze niż 60 dni
python3 routine/czysc_stare.py --dni 60 --dry  # najpierw zobacz, co usunie
git add -A && git commit -m "Czyszczenie starych wydań" && git push
```

Skrypt usuwa pliki wydań **wraz z ich katalogami grafik** i odbudowuje
`index.html` (tą samą logiką, której używa rutyna — czyta ją z instrukcji).
Uwaga: pełne odchudzenie repo wymagałoby przepisania historii gita — zwykłe
usunięcie wystarcza, by strona była czysta.

---

## Rutyny chmurowe

| Wydanie | Cron | Publikuje |
|---|---|---|
| Poranne | 7:00 (`0 5 * * *` UTC) | `wydania/…-rano-GGMM.html` |
| Wieczorne | 19:00 (`0 17 * * *` UTC) | `wydania/…-wieczor-GGMM.html` |

Model generujący każde wydanie jest logowany w sekcji **Logs** tego wydania.
Do repo pushują też inne rutyny (raport-finansowy) — dlatego zawsze
`git pull --rebase` przed własnym pushem.

---

*Grzyb Times — redagowane przez AI.*
