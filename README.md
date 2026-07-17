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
| `config.yaml` | **Konfiguracja, którą edytujesz Ty.** Kategorie, ile artykułów na kategorię, źródła. |
| `template.html` | Szablon wydania (HTML + CSS + JS). Placeholder `__DANE__` = miejsce na dane. |
| `routine/instrukcja.md` | Pełna instrukcja dla AI: research → redakcja → generacja → publikacja. |
| `index.html` | Auto-generowane archiwum wszystkich wydań (strona główna). |
| `wydania/` | Gotowe wydania: `RRRR-MM-DD-{rano\|wieczor}-GGMM.html`. |

**Cała logika jest w repo.** Rutyny to tylko cienki bootstrap („znajdź repo →
przeczytaj `routine/instrukcja.md` → wykonaj"). Zmiana czegokolwiek = commit do
repo, bez ruszania rutyn.

---

## Jak to działa

```
cron (7:00 / 19:00)  →  rutyna klonuje repo  →  czyta config.yaml + template.html
                                                        + routine/instrukcja.md
        ↓
  research w sieci (WebSearch) wg kategorii i źródeł z config.yaml
        ↓
  składa JSON z artykułami, wstrzykuje do template.html (podmiana __DANE__)
        ↓
  zapisuje wydania/RRRR-MM-DD-…​.html, aktualizuje index.html
        ↓
  git commit + push  →  GitHub Pages publikuje
```

Obrazy artykułów pochodzą z **Wikimedia Commons** (rutyna zamienia angielską frazę
`obraz.query` na hotlinkowalny URL). Zdjęć z serwisów newsowych nie da się użyć —
blokują hotlinking.

---

## Jak zmieniać gazetę

Edytujesz plik, robisz `git commit` + `git push`. Najbliższe wydanie użyje nowej
wersji. Nie musisz dotykać rutyn.

### Kategorie i liczba artykułów — `config.yaml`
```yaml
kategorie:
  - nazwa: Okładka          # pierwsza = wielki artykuł otwierający (najważniejszy news dnia)
    liczba: 1
  - nazwa: Inwestowanie
    liczba: 3               # 3 artykuły w tej kategorii
    zakres: "rynki, akcje, decyzje banków centralnych"
    wykres: preferowany     # preferowany | opcjonalny | nie
```
- Kolejność kategorii = ważność (pierwsza na górze gazety).
- `liczba` = ile artykułów w danej kategorii. Łączna liczba wydania = suma `liczba`.
- Kategorię możesz dodać, usunąć lub przestawić.

### Źródła — `config.yaml`
```yaml
zrodla_pierwotne:      # link każdego artykułu MUSI pochodzić z jednej z tych domen
  - reuters.com
  - bloomberg.com
```

### Wygląd — `template.html`
Motyw jasny/ciemny, siatka artykułów, filtry kategorii, interaktywne wykresy
(tooltip po najechaniu), animacje. Zmiana stylu = edycja CSS w `<style>`.

### Proces redakcyjny — `routine/instrukcja.md`
Ton, długość, zasady doboru zdjęć, format wykresów. To „brief redakcyjny" dla AI.

---

## Publikacja ręczna / lokalny podgląd

Podgląd: otwórz dowolny plik z `wydania/` w przeglądarce.

Zmiany wypychasz normalnie:
```bash
git add -A
git commit -m "opis zmiany"
git push
```
> Uwaga: `&&`, nie `&` — `git commit -m "x" && git push`.

Repo używa uwierzytelniania SSH (`git@github.com:…`). Jeśli `git push` zwraca
`Permission denied (publickey)`, Twój klucz z tej maszyny nie jest dodany na
GitHubie — dodaj klucz publiczny w Settings → SSH keys (albo jako deploy key
z prawem zapisu).

---

## Rutyny chmurowe

| Wydanie | Godzina (cron) | Publikuje |
|---|---|---|
| Poranne | 7:00 (`0 5 * * *` UTC) | `wydania/…-rano-GGMM.html` |
| Wieczorne | 19:00 (`0 17 * * *` UTC) | `wydania/…-wieczor-GGMM.html` |

Znacznik `GGMM` w nazwie pliku pozwala opublikować **kilka wydań tego samego typu**
w ciągu dnia. Rutynami zarządza się przez API Claude Code (RemoteTrigger) — zmiana
potrzebna tylko przy zmianie godziny lub typu wydania.

---

*Grzyb Times — redagowane przez AI.*
