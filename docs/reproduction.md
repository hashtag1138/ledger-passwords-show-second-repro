# Reproduction

## Commandes

Build :

```bash
./repro build
```

Repro complète :

```bash
./repro test
```

## Ce que fait `./repro build`

- clone `LedgerHQ/app-passwords` au commit figé
- prépare deux worktrees sous `artifacts/build/`
- applique le patch sur la variante `patched`
- compile les deux variantes avec l'image Docker Ledger builder

## Ce que fait `./repro test`

- lance Speculos sur `original`
- joue les cas de repro
- relance Speculos sur `patched`
- rejoue les mêmes cas
- génère un rapport comparatif Markdown + JSON

## Cas couverts

1. contrôle : un seul identifiant poussé via APDU, `show first`
2. crash principal : deux identifiants valides poussés via APDU, `show second`
3. preuve device-only : création UI-only de deux identifiants, `type second`, puis `show second`

Le cas `device-only` automatisé utilise `a` et `b` pour rester stable côté clavier Nano piloté automatiquement. Le bug s'étend cependant au scénario réel `sofian terki` + `abc`, car la cause racine est une erreur d'indexation de liste et non le contenu des surnoms.

## Sorties

- rapport Markdown : `artifacts/reports/latest.md`
- rapport JSON : `artifacts/reports/latest.json`
- logs bruts Speculos : `artifacts/logs/<run-id>/`
