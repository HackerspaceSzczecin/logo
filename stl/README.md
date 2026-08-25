# Modele 3D (druk)

Projekty do druku 3D z logo HASZCZE. Pliki `.3mf` to projekty Bambu
Studio (kontener zip: siatka + ustawienia druku), a nie gołe `.stl` -
folder nazywa się `stl/` z przyzwyczajenia.

- `HaszczeZQR.3mf` - okrągła płytka 240 mm z logo i kodem QR
- `SameHaszcze.3mf` - sam kontur logo z napisem, 140 x 154 mm

## Podgląd

- `viewer.html` - przeglądarka 3D wszystkich modeli z tego folderu:
  otwórz plik w przeglądarce (działa z `file://`, bez serwera i bez
  internetu - siatki są wbudowane w plik). Przeciąganie obraca, kółko
  zoomuje, prawy przycisk (albo shift) przesuwa. Panel z boku pokazuje
  wymiary, liczbę trójkątów i commit, na którym stoi dany `.3mf`.
- `previews/*.png` - statyczne rendery, po jednym na model. Skrót
  commita jest w nazwie pliku (`SameHaszcze-dd1505e.png`) i w podpisie
  na obrazku; jeśli kopia robocza `.3mf` różni się od commita, nazwa
  dostaje jeszcze `-dirty`.

## Regeneracja

Oba podglądy są **generowane** - nie edytuj ich ręcznie. Po dorzuceniu
albo podmianie `.3mf` uruchom:

```bash
python3 scripts/stl_preview.py         # przebuduj stl/viewer.html
python3 scripts/stl_preview.py --png   # + re-render stl/previews/*.png
                                       # (potrzebuje Chrome pod Windows
                                       # przez WSL, jak scripts/regen.py)
```

Skrypt sam znajduje wszystkie `.3mf` w tym folderze, czyta siatkę samym
stdlibem Pythona 3 i wpisuje w podglądy commit, na którym stoi każdy
plik (z dopiskiem "zmieniony", jeśli kopia robocza różni się od
commita - żeby render nie udawał stanu, którego nie ma w historii).
Przy `--png` czyści też `previews/` ze wszystkiego, co nie jest
renderem aktualnych modeli: rendery starych commitów i modeli, których
już nie ma w `stl/`, znikają zamiast zalegać obok nowych.

Renderowanie PNG odbywa się przez ten sam `viewer.html` w trybie
`?shot=<nazwa>`: headless Chrome robi zrzut z ustalonego kąta, więc
podgląd i statyczny render zawsze pokazują to samo.
