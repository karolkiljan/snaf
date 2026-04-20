---
name: snaf-context-threshold
description: >
  Ustawia próg tokenów dla context watch. Użyj gdy chcesz zmienić próg ostrzeżenia
  o dużym kontekście, wywołujesz /snaf-context-threshold lub podajesz liczbę tokenów.
  Przykład: /snaf-context-threshold 40000
argument-hint: Token count (integer, e.g. 40000) — "off" disables, "on" re-enables
disable-model-invocation: true
---

## Wykonanie

Argument: `$ARGUMENTS`.

Docelowy plik: `~/.claude/.snaf-context-threshold` (nowa wartość trafia tu, nie do env w settings.json — env nie dociera do child procesów hooków).

### Przypadek 1 — argument to liczba całkowita > 0

Zapisz wartość do `~/.claude/.snaf-context-threshold` (plik tekstowy, jedna liczba).

Tool: `Write` z zawartością tej liczby (bez nowej linii dodatkowej, bez whitespace).

Potwierdź:
```
Próg ustawiony: {wartość} tokenów. Plik: ~/.claude/.snaf-context-threshold.
Działać natychmiast — Claude Code restart niepotrzebny.
```

### Przypadek 2 — argument to `off`

Całkowite wyłączenie context_watch (persona snaf dalej działać).

Tool: `Write` pustego pliku do `~/.claude/.snaf-context-watch-off` — hook czyta istnienie pliku, treść obojętna.

Potwierdź:
```
Context watch wyłączony. Plik flag: ~/.claude/.snaf-context-watch-off.
Żeby włączyć: /snaf-context-threshold on (albo usuń plik).
```

### Przypadek 3 — argument to `on`

Wznowienie context_watch (usunięcie pliku flag).

Tool: `Bash` → `rm -f ~/.claude/.snaf-context-watch-off`.

Potwierdź:
```
Context watch włączony z powrotem. Próg: bieżąca wartość z .snaf-context-threshold (albo default 85000).
```

### Przypadek 4 — argument pusty lub nieznany

Pokaż stan:
1. Czy context_watch wyłączony? Read `~/.claude/.snaf-context-watch-off` — jeśli istnieje → „WYŁĄCZONY".
2. Aktualny próg:
   - Read `~/.claude/.snaf-context-threshold` → jeśli istnieje i zawiera liczbę → ta wartość
   - Else env `SNAF_CONTEXT_THRESHOLD` (prawdopodobnie pusty)
   - Else default `85000`
3. Pokaż użycie: `/snaf-context-threshold <liczba>`, `/snaf-context-threshold off`, `/snaf-context-threshold on`.

## Prawa

- Nie pisz do `settings.json` — env tam ustawiony NIE dociera do hook child procesów. Plik flag jedyna pewna droga.
- Nie modyfikuj `.snaf-mode` — to osobny opt-out (persona), ortogonalny do context_watch.
- Nie twórz innych plików niż dwa wymienione (`.snaf-context-threshold`, `.snaf-context-watch-off`).
- Nie wymagaj restartu Claude Code — plik flag działa natychmiast, następny Stop hook go zobaczy.

## Przykłady

```
/snaf-context-threshold 150000   # podnieś próg
/snaf-context-threshold 40000    # wczesne ostrzeżenie
/snaf-context-threshold off      # wyłącz zupełnie
/snaf-context-threshold on       # włącz z powrotem
/snaf-context-threshold          # pokaż stan
```
