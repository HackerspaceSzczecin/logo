# Logo Hackerspace Szczecin (HASZCZE)

Wektorowe wersje logo. Zobacz też [AGENTS.md](AGENTS.md) - notatki dla
osób (i agentów) pracujących nad tym repo.

## Pliki

- `haszcze-logo.svg` - źródło prawdy: dokładny wektor, czarny `#1A1A1A`
  na przezroczystym tle
- `haszcze-logo-supported-A.svg` - niezależny wariant projektowy: ten sam
  wektor z poprzeczką podtrzymującą literę `A`
- `haszcze-logo.png` - czysty raster wyrenderowany z `haszcze-logo.svg`
  (1254x1254, tło białe)
- `haszcze-logo-yellow-on-black.svg`,
  `haszcze-logo-supported-A-yellow-on-black.svg` - żółty `#F5C400` na tle
  `#1A1A1A` (paleta HaSzcze.eu)
- `haszcze-logo-stripes.svg`, `haszcze-logo-supported-A-stripes.svg` -
  emblemat wypełniony ukośnymi pasami żółto-czarnymi (nawiązanie do
  starego logo), napis jednolity czarny
- `preview.html` - strona z podglądem wszystkich wersji i przyciskami
  pobierania
- `email-signature/` - emblemat przycięty pod generator sygnatur e-mail
  (bez napisu); **uwaga:** PNG stamtąd jest hostowany na
  `haszcze.eu/brand/` i linkowany z wysłanych maili - szczegóły w
  [email-signature/README.md](email-signature/README.md)
- `scripts/` - `regen.py` odtwarza wszystkie powyższe pliki pochodne
  z dwóch źródłowych wektorów, patrz niżej

## Kolory

| Token     | Hex       |
| --------- | --------- |
| hs-yellow | `#F5C400` |
| hs-black  | `#1A1A1A` |

Wszystkie warianty SVG dzielą tę samą geometrię ścieżek - zmiana koloru to
podmiana atrybutu `fill`.

## Aktualizacja po edycji `haszcze-logo.svg` lub `haszcze-logo-supported-A.svg`

Te dwa pliki to jedyne źródła prawdy dla geometrii - edytowane ręcznie
(np. w Inkscape). Wszystko inne (wersje żółte, paski, raster, kadry w
`email-signature/`) to ich mechaniczne przekształcenia. Po edycji
któregoś z nich odtwórz pochodne pliki skryptem zamiast poprawiać je
ręcznie:

```bash
python3 scripts/regen.py          # SVG-e (bez zależności, sam stdlib)
python3 scripts/regen.py --png    # + re-render haszcze-logo.png i
                                   # email-signature/haszcze-emblem.png
                                   # (potrzebuje Chrome pod Windows przez WSL,
                                   # zob. email-signature/README.md)
```

Jeśli logo trzeba będzie kiedyś zwektoryzować od zera z nowego PNG (jak
przy pierwszym trace), potrzebne są `pillow`, `numpy` i `potracer`
(`pip install pillow numpy potracer`) - do samej regeneracji pochodnych
plików (`scripts/regen.py`) nic poza Pythonem 3 nie jest wymagane.
