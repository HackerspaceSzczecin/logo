# AGENTS.md - Logo HASZCZE (Hackerspace Szczecin)

Repo z logo HASZCZE (Hackerspace Szczecin): wektor i jego pochodne.

## Źródła prawdy

Dwa ręcznie edytowane pliki SVG, niezależne od siebie:

- `haszcze-logo.svg` - wersja standardowa
- `haszcze-logo-supported-A.svg` - wariant z poprzeczką podtrzymującą
  literę `A`

Wszystko inne w repo (warianty kolorystyczne, paski, raster PNG, kadry
w `email-signature/`) jest wygenerowane z tych dwóch plików przez
`scripts/regen.py`. Nie edytuj plików pochodnych ręcznie - po zmianie
któregoś źródła odtwórz je skryptem (`python3 scripts/regen.py`, patrz
README.md).

## Krytyczne: `email-signature/haszcze-emblem.png` jest produkcyjny

Ten konkretny plik jest hostowany pod `haszcze.eu/brand/` i ten adres
jest wypalony w sygnaturach już wysłanych maili. Nie usuwaj go, nie
przenoś, nie zmieniaj jego nazwy bez przeczytania
`email-signature/README.md` - tam jest opisane, co się stanie, jeśli
zniknie, i jak go odtworzyć w razie awarii.

## Konwencje

- Kolory: `#F5C400` (hs-yellow), `#1A1A1A` (hs-black) - paleta
  HaSzcze.eu.
- Wszystkie warianty kolorystyczne dzielą identyczną geometrię ścieżek -
  różni je tylko `fill` i ewentualnie `viewBox` (kadr).
- `scripts/regen.py` nie ma zależności poza stdlib Pythona 3 (własny,
  minimalny parser ścieżek SVG w `scripts/svgpath.py` - obsługuje tylko
  komendy M/L/H/V/C/Z, bo tylko takie realnie występują w tych plikach).
  Rendering PNG (`--png`) potrzebuje zewnętrznej przeglądarki
  (headless Chrome); jeśli jej nie znajdzie, skrypt zgłasza ostrzeżenie
  i pomija ten krok zamiast się wywalać.
- Jeśli zmieniasz geometrię źródłowego SVG, przed uruchomieniem
  `regen.py` warto zweryfikować, że próg podziału emblemat/napis
  (`EMBLEM_TEXT_SPLIT_Y` w `regen.py`, obecnie y=900) nadal trafia w
  pustą przerwę między nimi - w razie wątpliwości sprawdź bboxy
  podścieżek (patrz historia commitów tego repo dla przykładu takiej
  weryfikacji).
