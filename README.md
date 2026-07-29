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
| `routine/instrukcja.md` | Pełna instrukcja dla AI: research → redakcja → dane → publikacja. |
| `routine/buduj_wydanie.py` | Dane redakcji (JSON) + config + szablon → gotowe wydanie. Tu mieszkają pogoda, obrazy, kontrole jakości i metryki. |
| `routine/buduj_index.py` | Buduje `index.html` (archiwum) i woła `buduj_dane.py`. Uruchamiany przy każdej publikacji i przez hook pre-commit. |
| `routine/buduj_dane.py` | Wyłuskuje z wydań i raportów `dane/*.json` dla stron pochodnych. |
| `szukaj.html` · `kalendarz.html` · `angielski.html` | Strony pochodne (patrz niżej). Wspólna stylistyka: `assets/strony.css`. |
| `dane/` | Auto-generowane `szukaj.json`, `kalendarz.json`, `angielski.json`. **Nie edytuj ręcznie.** |
| `routine/czysc_stare.py` | Czyszczenie starych wydań (patrz niżej). |
| `index.html` | Auto-generowane archiwum (strona główna): sekcja raportów finansowych + wydania grupowane po dniach, w stopce numer wersji. |
| `routine/hooks/pre-commit` | Odświeża `index.html` przed każdym lokalnym commitem (patrz „Numer wersji"). |
| `wydania/` | Gotowe wydania `RRRR-MM-DD-{rano\|wieczor}-GGMM.html` + `wydania/img/` (pobrane grafiki artykułów). **Wydań nie edytujemy — jedyny wyjątek: automat dobiera grafiki do NAJNOWSZEGO wydania (patrz „Dwa środowiska"). Archiwalnych nie rusza nic.** |
| `.github/workflows/` | GitHub Actions: dobranie grafik po publikacji + nocna kontrola linków. |
| `routine/dobierz_obrazy.py` · `routine/sprawdz_wydanie.py` | Skrypty wołane przez Actions; obie da się uruchomić lokalnie. |
| `assets/kategorie/` | Zdjęcia bazowe kategorii (2–3 na kategorię, rotacja przeciw duplikatom). |
| `raport-template.html` | Szablon raportu finansowego (stylistyka gazety). Otwarty bez podstawionej treści pokazuje **podgląd szablonu**. |
| `routine/instrukcja-raport.md` | Instrukcja publikacji raportu dla rutyny raportowej (analiza i portfel zostają w jej prompcie — repo jest publiczne). |
| `routine/buduj_raporty.py` | Renderuje `raport-finansowy/*.md` → `.html` po `raport-template.html` (patrz niżej). |
| `raport-finansowy/` | Osobna rutyna: przeglądy rynku (niezależne od gazety). Źródło = `.md`, strona = zbudowany obok `.html`. |
| `.nojekyll` | Wyłącza Jekylla na GitHub Pages — całe repo to gotowy statyczny HTML. |

**Cała logika jest w repo.** Rutyny to cienki bootstrap („znajdź repo → przeczytaj
`routine/instrukcja.md` → wykonaj"). Zmiana czegokolwiek = commit, bez ruszania rutyn.

---

## Jak to działa

```
cron → rutyna klonuje repo → config.yaml + template.html + instrukcja.md
      ↓
uwagi czytelników (GitHub Issues „[Uwaga] …”) + wątki z poprzedniego wydania (follow-upy)
      ↓
research (WebSearch) wg kategorii i źródeł; rubryka ocen: realny skutek > skala > nowość
      ↓
redakcja: akapity, skróty, kwoty z ~PLN, tooltipy {{termin|wyjaśnienie}}, timestampy źródeł
      ↓
model zapisuje JEDEN plik /tmp/grzyb_dane.json (artykuły, literatura, wątki, logi)
      ↓
buduj_wydanie.py: dane → template (__DANE__), pogoda, og:image, kontrole jakości → logi
      ↓
buduj_index.py + git commit + push → GitHub Pages
```

Model nie pisze kodu budującego wydanie — cała mechanika i kontrole siedzą
w `routine/buduj_wydanie.py`. Wcześniej skrypt był wklejony w instrukcji i model
przepisywał go z palca przy każdym wydaniu: kosztowało to tokeny wyjścia, gubiło
polskie znaki w logach i po cichu zmieniało logikę kontroli.

### Obrazy (trzy warstwy, wszystkie automatyczne)
1. **og:image artykułu źródłowego** — skrypt pobiera grafikę newsa i commituje do
   `wydania/img/…`. **W praktyce nie działa:** środowisko rutyn siedzi za proxy,
   które przepuszcza tylko GitHub i API Anthropic, więc od 20.07.2026 pobrano
   0 grafik. Kod zostaje — sam się odblokuje, jeśli proxy się zmieni.
2. Realny obraz: **zdjęcie kategorii** z `assets/kategorie/` (rotacja 2–3 zdjęć).
3. Bonus: przeglądarka czytelnika może podmienić zdjęcie kategorii na trafniejsze
   z Wikimedia Commons (`obraz.query`) — to jedyna działająca ścieżka do zdjęcia
   związanego z konkretnym tematem.

### Funkcje wydania
„W skrócie" (jednozdaniowe streszczenia z kotwicami) · filtry kategorii (start:
Okładka) · badge „Aktualizacja" przy kontynuacjach · interaktywne wykresy (tylko
gdy źródło daje komplet danych) · kluczowe liczby · tooltipy trudnych terminów ·
czas czytania · timestamp publikacji u źródła · „Zgłoś uwagę" (GitHub Issue,
rutyna czyta je przy kolejnym wydaniu) · pogoda z Interii (klik → pełna prognoza) ·
nawigacja poprzednie/następne · sekcja **Logs** (diagnostyka rutyny, w tym model
generujący wydanie) · motyw jasny/ciemny · design „paper & ink" (mobile/tablet/desktop + druk).

### Dwa środowiska: rutyna i GitHub Actions

Ten system działa w dwóch miejscach o odwrotnych mocnych stronach:

| | Rutyna (sesja Claude Code w chmurze) | GitHub Actions |
|---|---|---|
| Model — wybiera, ocenia, redaguje | **tak** | nie, to goły skrypt |
| WebSearch / WebFetch | tak | brak |
| Zwykły ruch HTTP do dowolnej domeny | **nie** — proxy przepuszcza tylko GitHuba i API Anthropic | **tak** |
| Koszt | tokeny | darmowe minuty (repo publiczne) |

**Rutyna ma osąd, ale nie ma internetu. Actions ma internet, ale nie ma osądu.**
Stąd podział: co wymaga wyboru — rutyna; co mechaniczne, ale potrzebuje otwartej
sieci — Actions. Actions nigdy nie podejmuje decyzji redakcyjnej.

**`grafiki-wydania.yml`** (na push do `wydania/*.html`) — dokańcza publikację:
pobiera `og:image` ze stron źródłowych, dopisuje `obraz.plik`, przebudowuje archiwum
i commituje. Wchodzi **wyłącznie w najnowsze wydanie**; pilnują tego dwa niezależne
zabezpieczenia (workflow podaje tylko pliki z pusha, a `dobierz_obrazy.py` i tak
odmawia pracy na czymkolwiek poza najnowszym plikiem). Pętli commitów nie ma:
push wykonany wbudowanym `GITHUB_TOKEN` nie wyzwala kolejnych przebiegów — dlatego
świadomie nie podpinamy tu własnego PAT-a.

**`nocna-kontrola.yml`** (4:27 UTC) — niczego nie zmienia. Sprawdza spójność wydań
i czy linki źródeł żyją, a usterkę zgłasza jako issue `[Auto] Usterki w wydaniach`,
które rutyna czyta w KROK 0.5; gdy problem zniknie, sam je zamyka. **HTTP 403 nie
jest usterką** — Bloomberg i phys.org blokują boty na sprawnych stronach (19 z 50
sprawdzonych linków), więc liczą się tylko 404, 410 i brak domeny.

Kanał zwrotny jest ten sam co dla czytelników: automat znajduje martwy link, ale
nowego źródła nie wybiera — oddaje sprawę tam, gdzie jest model.

### Strony pochodne

Trzy statyczne strony żywiące się tym, co gazeta i raporty już wyprodukowały.
Budują się same przy każdej publikacji (`buduj_index.py` → `buduj_dane.py` → `dane/*.json`),
więc nie wymagają żadnej pracy od rutyn poza trzymaniem się formatu danych.

| Strona | Co pokazuje | Skąd bierze dane |
|---|---|---|
| `/szukaj.html` | Wyszukiwarka wszystkich artykułów (tytuł, skrót, kategoria), z podświetlaniem i filtrem kategorii; link prowadzi do kotwicy artykułu w wydaniu. Działa bez ogonków — „zelenski" znajdzie „Zełenski". | `artykuly[]` ze wszystkich wydań |
| `/kalendarz.html` | Zapowiedzi z terminami: dziś / w tygodniu / w miesiącu / później / bez daty + „minęło, sprawdź". | `watki` **najnowszego** wydania + `### Co obserwować` **najnowszego** raportu |
| `/angielski.html` | Wszystkie słowa i zwroty z rubryki „Angielski na dziś" — lista albo fiszki z powtórkami (pudełka Leitnera w `localStorage`). | `literatura.angielski` ze wszystkich wydań |

Kalendarium celowo czyta tylko najnowsze wydanie i najnowszy raport: obie rutyny
mają obowiązek przenosić otwarte pozycje dalej, więc te dwa pliki są pełnym,
aktualnym stanem obserwacji. Sięganie głębiej dawałoby wyłącznie duplikaty
i terminy, które redakcja świadomie porzuciła.

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

## Numer wersji

W stopce strony głównej jest `vN` — **numer commita na `main`**, który tę wersję
opublikował (link prowadzi do historii repo). Liczy go `buduj_index.py`:
`git rev-list --count HEAD` + 1, bo archiwum przebudowuje się tuż przed commitem
publikującym. Nie ma osobnego pliku z wersją, więc równoległe pushe rutyn nie
mają o co się pobić. Klon w środowisku rutyny bywa płytki i licznik wtedy kłamał
(29.07 rutyna wpisała `v52` przy 91 commitach), dlatego skrypt najpierw robi
`git fetch --unshallow`.

Warunek: `index.html` musi być przebudowany w tym samym commicie. Rutyny robią
to same (gazeta w KROKU 4, raport w KROKU 4). Dla commitów z lokalnej maszyny
pilnuje tego hook — **w świeżym klonie włącz go raz**:

```bash
git config core.hooksPath routine/hooks
```

---

## Raporty finansowe

Pełna procedura dla rutyny: **`routine/instrukcja-raport.md`** (rutyna czyta ją
z repo przed napisaniem raportu). Raport jest **ciągiem dalszym poprzedniego**:
każdy kończy się listą „Co obserwować” z terminami, a następny zaczyna od
sprawdzenia, co się z niej rozstrzygnęło — dzięki temu lista obserwacji żyje
w repo, a nie w prompcie rutyny, i się nie starzeje.

W skrócie — rutyna pisze **wyłącznie markdown**, jeden plik na raport:

```markdown
---
title: "Przegląd rynku – 28 lipca 2026"
date: 2026-07-28
---

# Przegląd rynku — 28 lipca 2026     ← pierwszy H1 jest wycinany (dubluje nagłówek strony)

> **Kontekst:** …
```

Nazwa pliku: `raport-finansowy/RRRR-MM-DD-nazwa.md` (data z przodu = kolejność
w archiwum; drugi raport tego samego dnia → sufiks `-2`). Potem:

```bash
python3 routine/buduj_raporty.py    # .md → .html po raport-template.html
python3 routine/buduj_index.py      # wpis w archiwum na stronie głównej
git add raport-finansowy index.html && git commit -m "Raport …" && git push
```

`buduj_raporty.py` bierze `title`/`date` z front mattera (H1 = temat bez daty,
dopisek w nawiasie → kicker, data → pasek pod nagłówkiem), renderuje markdown
i przelicza nawigację poprzedni/następny **we wszystkich** raportach. Konwerter
jest bez zależności i obsługuje: nagłówki, akapity, `**bold**`, `*kursywę*`,
`` `kod` ``, odnośniki, listy `-`/`1.`, cytaty `>`, tabele GFM i `---`.

Archiwum linkuje tylko raporty, które mają zbudowany `.html` — sam `.md` nie
wystarczy (zabezpieczenie przed 404).

---

## Rutyny chmurowe

| Rutyna | Cron (UTC) | Stan | Publikuje |
|---|---|---|---|
| Grzyb Times — poranne | `0 3 * * *` (5:00 PL) | włączona | `wydania/…-rano-GGMM.html` |
| Grzyb Times — wieczorne | `0 17 * * *` (19:00 PL) | wyłączona | `wydania/…-wieczor-GGMM.html` |
| Przegląd rynku i portfela | `0 6 1 * *` | wyłączona (na żądanie) | `raport-finansowy/…` |

Wszystkie chodzą na `claude-sonnet-5`. Model generujący wydanie jest logowany
w sekcji **Logs** (pole `model` w danych redakcji). Do repo pushują różne rutyny
— dlatego zawsze `git pull --rebase` przed własnym pushem.

**Okno świeżości dopasowuje się do kadencji:** `buduj_wydanie.py` liczy je jako
czas od poprzedniego wydania + 2 h (w granicach 12–36 h). Przy dwóch wydaniach
dziennie wychodzi ~12 h, przy jednym ~24 h — dlatego włączenie lub wyłączenie
wydania wieczornego nie wymaga zmian w instrukcji.

---

*Grzyb Times — redagowane przez AI.*
