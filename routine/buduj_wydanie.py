#!/usr/bin/env python3
"""Zbuduj wydanie „Grzyb Times": dane redakcji (JSON) + config.yaml + template.html → gotowa strona.

    python3 routine/buduj_wydanie.py rano /tmp/grzyb_dane.json

Rutyna pisze WYŁĄCZNIE dane redakcyjne (artykuły, literatura, wątki, własne logi),
a cała mechanika — nagłówek wydania, pogoda, obrazy, kontrole jakości, metryki
przebiegu — mieszka tutaj. Wcześniej ten kod był wklejony w routine/instrukcja.md
i model przepisywał go z palca przy każdym wydaniu: kosztowało to tokeny wyjścia,
gubiło polskie znaki w logach i po cichu zmieniało logikę kontroli.

Wynik: /tmp/grzyb_times.html + /tmp/grzyb_filename (nazwę bierze KROK 5 publikacji).
"""
import datetime
import glob
import io
import json
import os
import pathlib
import re
import subprocess
import sys
import urllib.parse
import urllib.request

REPO = pathlib.Path(__file__).resolve().parent.parent

UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
DNI = ['poniedziałek', 'wtorek', 'środa', 'czwartek', 'piątek', 'sobota', 'niedziela']
MIESIACE = ['', 'stycznia', 'lutego', 'marca', 'kwietnia', 'maja', 'czerwca',
            'lipca', 'sierpnia', 'września', 'października', 'listopada', 'grudnia']
PAYWALL = ('bloomberg.com',)
# `zrodlo.opublikowano` podajemy w czasie polskim (patrz instrukcja KROK 2), a
# wydanie znakujemy w UTC — bez tej strefy każdy artykuł „starzał się" o 2 h.
try:
    from zoneinfo import ZoneInfo
    TZ_PL = ZoneInfo('Europe/Warsaw')
except Exception:                                        # brak bazy tzdata
    TZ_PL = datetime.timezone(datetime.timedelta(hours=2))


def wczytaj_config() -> dict:
    try:
        import yaml
    except ImportError:
        subprocess.run("pip install pyyaml -q", shell=True)
        try:
            import yaml
        except ImportError:
            sys.exit("Brak pyyaml i nie dało się go doinstalować — nie odczytam config.yaml.")
    return yaml.safe_load((REPO / 'config.yaml').read_text(encoding='utf-8'))


# ------------------------------------------------------------------ pogoda ---

def pogoda_z_interii(pogoda: dict, log) -> None:
    """Aktualna pogoda parsowana ze strony Interii (zero tokenów LLM).

    Gdy się nie uda, pole zostaje puste i przeglądarka czytelnika użyje Open-Meteo."""
    try:
        url = pogoda.get("prognoza_url", "")
        if "pogoda.interia.pl" not in url:
            return
        html = urllib.request.urlopen(urllib.request.Request(url, headers=UA),
                                      timeout=15).read().decode("utf-8", "ignore")
        temp = re.search(r'weather-currently-temp-strict">\s*(-?\d+)°C', html)
        if not temp:
            return
        opis_m = re.search(r'weather-currently-icon[^"]*"\s*\n?\s*title="([^"]+)"', html)
        opis = (opis_m.group(1) if opis_m else "").strip()
        low = opis.lower()
        emoji = ("⛈️" if "burz" in low else "🌧️" if "deszcz" in low or "opady" in low else
                 "🌨️" if "śnieg" in low else "🌫️" if "mgł" in low else
                 "☀️" if "słonecznie" in low or "bezchmurnie" in low else
                 "🌤️" if "małe" in low else "⛅" if "umiarkowane" in low else
                 "☁️" if "zachmurzenie" in low or "pochmurno" in low else "")
        pogoda["aktualna"] = f"{pogoda.get('miasto', '')} {emoji} {temp.group(1)}°C".replace("  ", " ").strip()
        if opis:
            pogoda["opis"] = opis
    except Exception as ex:
        log("info", f"Pogoda z Interii nieudana ({type(ex).__name__}) — przeglądarka użyje Open-Meteo.")


# ------------------------------------------------------------------ obrazy ---

def pobierz_og_image(artykuly: list, katalog: pathlib.Path, prefix: str, log,
                     kontekst: str = "") -> None:
    """Warstwa 1 obrazów: og:image artykułu źródłowego → repo (ten sam origin).

    Porażka = artykuł zostaje przy zdjęciu swojej kategorii; przeglądarka może je
    jeszcze podmienić przez Wikimedię wg `obraz.query`.

    Artykuły, które mają już `obraz.plik`, są pomijane — dzięki temu funkcja jest
    idempotentna i może ją wywołać po publikacji `routine/dobierz_obrazy.py`
    (środowisko rutyny nie ma wyjścia HTTP w świat, GitHub Actions ma)."""
    try:
        from PIL import Image
    except ImportError:
        subprocess.run("pip install pillow -q", shell=True)
        try:
            from PIL import Image
        except ImportError:
            log("info", "Brak Pillow — pomijam og:image, artykuły dostaną zdjęcia kategorii.")
            return

    bledy = {}
    for i, a in enumerate(artykuly):
        if a["obraz"].get("plik"):
            continue                                      # grafika już jest
        try:
            html = urllib.request.urlopen(
                urllib.request.Request(a["zrodlo"]["url"], headers=UA), timeout=12
            ).read(400000).decode('utf-8', 'ignore')
            m = (re.search(r'property=["\']og:image["\'][^>]*content=["\']([^"\']+)', html) or
                 re.search(r'content=["\']([^"\']+)["\'][^>]*property=["\']og:image["\']', html))
            if not m:
                continue
            src = m.group(1).replace('&amp;', '&')
            if src.startswith('//'):
                src = 'https:' + src
            raw = urllib.request.urlopen(urllib.request.Request(src, headers=UA), timeout=12).read()
            im = Image.open(io.BytesIO(raw)).convert('RGB')
            if im.width < 400 or im.height < 220:
                continue                                  # logo/ikonka — pomiń
            im.thumbnail((900, 900))
            katalog.mkdir(parents=True, exist_ok=True)
            im.save(katalog / f"art-{i}.jpg", 'JPEG', quality=78, optimize=True)
            a["obraz"]["plik"] = f"/wydania/img/{prefix}/art-{i}.jpg"
        except Exception as ex:
            klucz = str(ex)[:120] or type(ex).__name__
            bledy[klucz] = bledy.get(klucz, 0) + 1

    udane = sum(1 for a in artykuly if a["obraz"].get("plik"))
    print(f"Obrazy ze źródeł (og:image): {udane}/{len(artykuly)}")
    if udane < len(artykuly):
        diag = ""
        if bledy:
            top = max(bledy, key=bledy.get)
            diag = f" Najczęstszy błąd ({bledy[top]}×): {top}"
        log("warning" if (udane == 0 and bledy) else "info",
            f"Obrazy: {udane}/{len(artykuly)} ze źródeł; pozostałe = zdjęcia kategorii."
            f"{kontekst}{diag}")


# ---------------------------------------------------------------- kontrole ---

def okno_swiezosci(now: datetime.datetime) -> int:
    """Ile godzin wstecz sięga wydanie: czas od POPRZEDNIEGO wydania + 2 h zapasu.

    Przy dwóch wydaniach dziennie wychodzi ~12 h, przy jednym ~24 h — reguła sama
    dopasowuje się do kadencji publikacji, zamiast karać wydanie za cudzy grafik.
    Granice 12–36 h chronią przed absurdem po dłuższej przerwie w wydaniach."""
    pliki = sorted((REPO / 'wydania').glob('*.html'))
    for plik in reversed(pliki):
        m = re.match(r'(\d{4}-\d{2}-\d{2})-(?:rano|wieczor)-(\d{2})(\d{2})$', plik.stem)
        if not m:
            continue
        poprzednie = datetime.datetime.strptime(
            f'{m.group(1)} {m.group(2)}:{m.group(3)}', '%Y-%m-%d %H:%M'
        ).replace(tzinfo=datetime.timezone.utc)
        return min(36, max(12, round((now - poprzednie).total_seconds() / 3600) + 2))
    return 24


def parsuj_date(s: str):
    """(datetime w czasie polskim, czy_zna_godzine) albo (None, False)."""
    s = (s or "").strip()
    for fmt, ma_czas in (("%d.%m.%Y %H:%M:%S", True), ("%d.%m.%Y %H:%M", True),
                         ("%Y-%m-%dT%H:%M:%S", True), ("%Y-%m-%d %H:%M", True),
                         ("%d.%m.%Y", False), ("%Y-%m-%d", False)):
        try:
            return datetime.datetime.strptime(s, fmt).replace(tzinfo=TZ_PL), ma_czas
        except ValueError:
            pass
    return None, False


def kontrola_swiezosci(artykuly: list, cfg: dict, now: datetime.datetime, log) -> None:
    """Wiek źródeł względem okna wydania — RAPORT ZBIORCZY, nie wpis na artykuł.

    Wpis per artykuł zalewał sekcję Logs (audyt 23–29.07: 15–20 wpisów na wydanie,
    przez co realne błędy ginęły w szumie)."""
    okno = okno_swiezosci(now)
    weekend = now.astimezone(TZ_PL).weekday() >= 5
    stare, bez_godziny, niejasne = [], [], []
    for a in artykuly:
        opublikowano = (a.get("zrodlo") or {}).get("opublikowano", "")
        if not opublikowano:
            continue                                      # brak pola jest dozwolony
        dt, ma_czas = parsuj_date(opublikowano)
        limit = max(48, okno) if (weekend and a.get("kategoria") == "Inwestowanie") else okno
        if dt is None:
            niejasne.append(a["tytul"])
        elif ma_czas:
            wiek = (now - dt).total_seconds() / 3600
            if wiek > limit:
                stare.append((wiek, a["tytul"]))
        else:
            dni = (now.astimezone(TZ_PL).date() - dt.date()).days
            if dni * 24 > limit:
                stare.append((dni * 24.0, a["tytul"]))
            else:
                bez_godziny.append(a["tytul"])

    if stare:
        stare.sort(reverse=True)
        log("warning", f"Świeżość: {len(stare)} z {len(artykuly)} art. poza oknem {okno} h — "
                       f"najstarszy „{stare[0][1][:70]}” ({stare[0][0]:.0f} h).")
    if bez_godziny:
        log("info", f"{len(bez_godziny)} art. ma datę źródła bez godziny — okna {okno} h nie da się "
                    f"potwierdzić. Podawaj `opublikowano` z GG:MM.")
    if niejasne:
        log("warning", f"{len(niejasne)} art. z niejasnym timestampem źródła (np. „{niejasne[0][:50]}”) — "
                       f"format DD.MM.YYYY[ GG:MM].")
    print(f"Okno świeżości: {okno} h | poza oknem: {len(stare)} | bez godziny: {len(bez_godziny)}")


def kontrola_zrodel(artykuly: list, cfg: dict, log) -> None:
    """`zrodlo.url` ma być KONKRETNYM artykułem z listy `zrodla_pierwotne`.

    Audyt 29.07: dwa artykuły linkowały samą stronę główną sciencedaily.com, jeden
    dawał 404 (URL złożony z wzorca, nie skopiowany z wyników wyszukiwania)."""
    domeny = [str(d).split('/')[0].lower().removeprefix('www.')
              for d in (cfg.get('zrodla_pierwotne') or [])]
    bez_artykulu, obce, paywall = [], [], []
    for a in artykuly:
        url = ((a.get("zrodlo") or {}).get("url") or "")
        czesci = urllib.parse.urlparse(url)
        host = czesci.netloc.lower().removeprefix('www.')
        if len(czesci.path.strip('/')) < 10:
            bez_artykulu.append(a["tytul"])
        if domeny and host and not any(host == d or host.endswith('.' + d) for d in domeny):
            obce.append(f"{host} („{a['tytul'][:40]}”)")
        if any(host.endswith(d) for d in PAYWALL):
            paywall.append(a["tytul"])

    if bez_artykulu:
        log("error", f"{len(bez_artykulu)} art. linkuje stronę główną/kategorię zamiast artykułu "
                     f"(np. „{bez_artykulu[0][:60]}”) — URL kopiuj 1:1 z wyników wyszukiwania.")
    if obce:
        log("error", f"Źródła spoza config.zrodla_pierwotne: {', '.join(obce[:3])}"
                     f"{f' i {len(obce) - 3} inne' if len(obce) > 3 else ''}.")
    if len(paywall) > len(artykuly) / 3:
        log("warning", f"Paywall: {len(paywall)} z {len(artykuly)} linków prowadzi do "
                       f"{'/'.join(PAYWALL)} — czytelnik ich nie otworzy.")


def kontrola_redakcji(artykuly: list, cfg: dict, log) -> None:
    """Kategorie, obraz okładki, liczba akapitów i liczba artykułów wg config.yaml."""
    poprawne = {k['nazwa'] for k in cfg['kategorie']}
    for a in artykuly:
        if a["kategoria"] not in poprawne:
            log("error", f"Nieznana kategoria „{a['kategoria']}” (artykuł „{a['tytul']}”). "
                         f"Użyj DOKŁADNEJ nazwy z config: {sorted(poprawne)}.")
        if a["obraz"].get("kategoria") and a["obraz"]["kategoria"] not in poprawne:
            log("error", f"Nieznana obraz.kategoria „{a['obraz']['kategoria']}” "
                         f"(artykuł „{a['tytul']}”) — użyj DOKŁADNEJ nazwy z config.")

    if artykuly and not artykuly[0]["obraz"].get("kategoria"):
        log("warning", "Artykuł okładkowy bez obraz.kategoria — dostanie neutralny glob "
                       "zamiast zdjęcia kategorii tematycznej.")

    limit = cfg['wydanie'].get('akapity', 3)
    for a in artykuly:
        n = len(a.get("akapity") or [])
        if n > limit:
            log("warning", f"Artykuł „{a['tytul']}”: {n} akapitów, config dopuszcza najwyżej {limit}.")

    # `liczba` to CEL i górna granica: nadmiar = realny problem (warning),
    # niedobór przy chudym materiale jest OK (info — ślad bez fałszywego alarmu).
    from collections import Counter
    oczekiwane = {k['nazwa']: k.get('liczba', 1) for k in cfg['kategorie']}
    zlozone = Counter(a['kategoria'] for a in artykuly)
    for kat, ile_ma_byc in oczekiwane.items():
        ile = zlozone.get(kat, 0)
        if ile > ile_ma_byc:
            log("warning", f"Kategoria „{kat}”: złożono {ile} art., config dopuszcza najwyżej {ile_ma_byc}.")
        elif ile < ile_ma_byc:
            log("info", f"Kategoria „{kat}”: złożono {ile} art. z {ile_ma_byc} w configu — "
                        f"mniej przy chudym materiale, bez dopychania wodą.")


def kontrola_watkow(watki: list, log) -> None:
    """`watki` zasilają follow-upy następnego wydania i stronę kalendarza, więc
    mają być obiektami `{data, temat, sprawdzic}` — z gołego zdania trzeba datę
    zgadywać regexem."""
    stare = [w for w in watki if not isinstance(w, dict)]
    if stare:
        log("warning", f"{len(stare)} z {len(watki)} wątków w starym formacie (goły tekst) — "
                       f"podawaj obiekty {{\"data\": \"RRRR-MM-DD\", \"temat\": …, \"sprawdzic\": …}}.")
    bez_daty = [w for w in watki if isinstance(w, dict) and not w.get("data")]
    if len(bez_daty) == len(watki) and watki:
        log("info", "Żaden wątek nie ma pola `data` — kalendarium pokaże je bez terminu.")


def kontrola_literatury(literatura: dict, cfg: dict, log) -> None:
    """Sekcja składana z własnej wiedzy modelu — ma być kompletna (4/4) w każdym wydaniu."""
    if not (cfg.get('literatura') or {}).get('wlaczona'):
        return
    braki = [k for k in ('cytat', 'przyslowie', 'wiersz', 'angielski') if not literatura.get(k)]
    if braki:
        log("warning", f"Literatura niekompletna — brak: {', '.join(braki)}. "
                       f"Ta sekcja nie zależy od sieci, składasz ją z własnej wiedzy.")


# --------------------------------------------------------------- metryki -----

def metryki(log) -> None:
    """Czas wykonania (od znacznika z KROK 0) i zużycie tokenów z transkryptu sesji."""
    fmt = lambda n: f"{n:,}".replace(",", " ")
    try:
        start = int(pathlib.Path('/tmp/grzyb_start_epoch').read_text().strip())
        sekundy = max(0, int(datetime.datetime.now().timestamp()) - start)
        log("info", f"Czas wykonania rutyny: {sekundy // 60} min {sekundy % 60} s "
                    f"(od startu KROK 0 do wygenerowania wydania).")
    except Exception:
        pass                                              # brak znacznika — pomiń

    # Best-effort: tura budująca wydanie nie jest jeszcze w transkrypcie, stąd „≈".
    try:
        sid = os.environ.get('CLAUDE_CODE_SESSION_ID', '') or os.environ.get('CLAUDE_SESSION_ID', '')
        kandydaci = glob.glob(os.path.expanduser('~/.claude/projects/**/*.jsonl'), recursive=True)
        plik = (next((p for p in kandydaci if sid and sid in p), None)
                or (max(kandydaci, key=os.path.getmtime) if kandydaci else None))
        we = wy = cache = 0
        if plik:
            for linia in pathlib.Path(plik).read_text(errors='ignore').splitlines():
                try:
                    u = (json.loads(linia).get('message') or {}).get('usage') or {}
                except Exception:
                    continue
                we += u.get('input_tokens', 0)
                wy += u.get('output_tokens', 0)
                cache += u.get('cache_read_input_tokens', 0) + u.get('cache_creation_input_tokens', 0)
        if wy or we:
            log("info", f"Zużyte tokeny (≈): wyjście {fmt(wy)}, wejście {fmt(we)}, "
                        f"kontekst z cache {fmt(cache)}.")
        else:
            log("info", "Zużycie tokenów: niedostępne w tym środowisku (brak transkryptu sesji).")
    except Exception as ex:
        log("info", f"Zużycie tokenów: niedostępne ({type(ex).__name__}).")


# ------------------------------------------------------------------ budowa ---

def main() -> None:
    if len(sys.argv) < 3 or sys.argv[1] not in ('rano', 'wieczor'):
        sys.exit("Użycie: python3 routine/buduj_wydanie.py <rano|wieczor> <dane.json>")
    wydanie, plik_danych = sys.argv[1], pathlib.Path(sys.argv[2])
    if not plik_danych.exists():
        sys.exit(f"Brak pliku danych {plik_danych} — najpierw zapisz JSON redakcji (KROK 3).")

    try:
        redakcja = json.loads(plik_danych.read_text(encoding='utf-8'))
    except json.JSONDecodeError as ex:
        sys.exit(f"Niepoprawny JSON w {plik_danych}: {ex}")

    cfg = wczytaj_config()
    now = datetime.datetime.now(datetime.timezone.utc)     # przeglądarka przeliczy na czas PL
    lokalnie = now.astimezone(TZ_PL)
    etykieta = 'Wydanie poranne' if wydanie == 'rano' else 'Wydanie wieczorne'

    dane = {
        "tytul": cfg['wydanie']['tytul'],
        "kicker": f"{etykieta} · Redagowane przez AI",
        "data_iso": now.strftime('%Y-%m-%dT%H:%M:%SZ'),
        # fallback (UTC), gdyby JS/Intl zawiódł — normalnie formatuje to przeglądarka
        "data_wydania": (f"{DNI[now.weekday()]}, {now.day} {MIESIACE[now.month]} "
                         f"{now.year}, {now.strftime('%H:%M')}"),
        "numer": etykieta,
        "artykuly": redakcja.get("artykuly") or [],
        "literatura": redakcja.get("literatura") or {},
        "logi": [],
        "watki": redakcja.get("watki") or [],
        "pogoda": cfg.get('pogoda') or {},
    }

    def log(poziom, wiadomosc):
        dane["logi"].append({"poziom": poziom, "wiadomosc": wiadomosc})
        print(f"  LOG[{poziom}] {wiadomosc}")

    if redakcja.get("model"):
        log("info", f"Model rutyny: {redakcja['model']}")
    else:
        log("warning", "Brak pola `model` w danych redakcji — nie wiadomo, który model złożył wydanie.")
    for wpis in redakcja.get("logi") or []:
        log(wpis.get("poziom", "info"), wpis.get("wiadomosc", ""))

    if not dane["artykuly"]:
        sys.exit("Zero artykułów w danych redakcji — nie ma z czego budować wydania.")

    # Normalizacja obrazu: `plik` dokłada niżej og:image, `kategoria` tylko okładka.
    for a in dane["artykuly"]:
        obraz = a.get("obraz") or {}
        a["obraz"] = {"query": obraz.get("query") or "", "alt": obraz.get("alt") or a["tytul"]}
        if obraz.get("kategoria"):
            a["obraz"]["kategoria"] = obraz["kategoria"]

    # Sonda łączności: środowisko rutyny siedzi za proxy, które przepuszcza tylko
    # wybrane domeny (github.com, API Anthropic). Jedna próba zamiast kilkunastu
    # cichych porażek — od 20.07.2026 wychodzi negatywnie w każdym przebiegu.
    siec = True
    try:
        urllib.request.urlopen(urllib.request.Request('https://www.wikimedia.org', headers=UA),
                               timeout=10).read(200)
    except Exception as ex:
        siec = False
        log("info", f"Brak wyjścia HTTP w świat ({type(ex).__name__}) — stan znany i stały dla tego "
                    f"środowiska; obrazy = zdjęcia kategorii, pogoda = Open-Meteo w przeglądarce.")

    if siec:
        pogoda_z_interii(dane["pogoda"], log)
        katalog_img = f"{now.date()}-{wydanie}"           # jak nazwa pliku wydania: UTC
        pobierz_og_image(dane["artykuly"], REPO / 'wydania' / 'img' / katalog_img,
                         katalog_img, log)

    kontrola_redakcji(dane["artykuly"], cfg, log)
    kontrola_zrodel(dane["artykuly"], cfg, log)
    kontrola_swiezosci(dane["artykuly"], cfg, now, log)
    kontrola_watkow(dane["watki"], log)
    kontrola_literatury(dane["literatura"], cfg, log)
    metryki(log)

    # Higiena: publikujemy logi jednego przebiegu, bez powtórek.
    widziane = set()
    dane["logi"] = [l for l in dane["logi"]
                    if (l["poziom"], l["wiadomosc"]) not in widziane
                    and not widziane.add((l["poziom"], l["wiadomosc"]))]

    szablon = (REPO / 'template.html').read_text(encoding='utf-8')
    out = szablon.replace('__DANE__', json.dumps(dane, ensure_ascii=False, indent=2))
    # Blok demo (Lorem Ipsum do podglądu szablonu) nie ma prawa trafić do wydania.
    out = re.sub(r'/\* DEMO-START.*?DEMO-END \*/', '/* dane produkcyjne */', out, flags=re.S)
    assert '__DANE__' not in out, "Szablon nie podstawił danych (__DANE__)."
    assert 'DEMO-START' not in out, "W wydaniu został blok demo."

    nazwa = f"{now.date()}-{wydanie}-{now.strftime('%H%M')}.html"
    pathlib.Path('/tmp/grzyb_times.html').write_text(out, encoding='utf-8')
    pathlib.Path('/tmp/grzyb_filename').write_text(nazwa, encoding='utf-8')

    oczekiwane = sum(k.get('liczba', 1) for k in cfg['kategorie'])
    print(f"Artykułów: {len(dane['artykuly'])} (config: {oczekiwane}) | logów: {len(dane['logi'])}")
    print(f"OK — {len(out):,} bajtów | plik: {nazwa}")


if __name__ == '__main__':
    main()
