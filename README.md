# ledger-passwords-show-second-repro

Repo autonome pour reproduire, documenter et valider le correctif du crash `show second` dans `LedgerHQ/app-passwords`.

## Objectif

Ce repo :

- clone `LedgerHQ/app-passwords` à un commit figé ;
- build une variante `original` et une variante `patched` ;
- lance Speculos ;
- exécute des scénarios de repro `push-style` et `device-only` ;
- génère un rapport unique comparant `original` vs `patched`.

Le repo ne dépend pas du companion actuel pour pousser les metadata : les tests parlent directement APDU à Speculos, ce qui garde la repro simple et autonome.

## Prérequis

- `git`
- `docker`
- `python3` >= `3.11`

## Commandes

Build :

```bash
./repro build
```

Test complet :

```bash
./repro test
```

Build + test :

```bash
./repro all
```

## Sorties

- build original : `artifacts/build/original/app-passwords/bin/app.elf`
- build patché : `artifacts/build/patched/app-passwords/bin/app.elf`
- manifest de build : `artifacts/build/manifest.json`
- dernier rapport : `artifacts/reports/latest.md`
- dernier rapport JSON : `artifacts/reports/latest.json`
- logs Speculos : `artifacts/logs/<run-id>/`

## Documentation

- vue d’ensemble : `docs/overview.md`
- reproduction : `docs/reproduction.md`
- cause racine : `docs/root-cause.md`
- patch expliqué : `docs/patch-explained.md`
- patch prêt à appliquer : `patches/app-passwords/0001-fix-show-second-index.patch`
