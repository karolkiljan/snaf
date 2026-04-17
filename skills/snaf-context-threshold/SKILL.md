---
name: snaf-context-threshold
description: >
  Ustawia próg tokenów dla context watch. Użyj gdy chcesz zmienić próg ostrzeżenia
  o dużym kontekście, wywołujesz /snaf-context-threshold lub podajesz liczbę tokenów.
  Przykład: /snaf-context-threshold 40000
---

## Wykonanie

Args zawiera nową wartość progu (liczba całkowita).

Użyj Skill tool z `update-config` żeby zaktualizować `"SNAF_CONTEXT_THRESHOLD"` w sekcji `"env"` w `settings.local.json` aktualnego projektu.

Uwaga: zmiana działa per-projekt. Żeby zmienić globalnie dla wszystkich projektów — zaktualizuj `~/.claude/settings.json` zamiast `settings.local.json`.

Po zmianie potwierdź w stylu orkowym: `Próg ustawiony: {nowa_wartość} tokenów.`

Jeśli args puste lub nie jest liczbą: pokaż aktualną wartość z pliku i powiedz jak użyć.
