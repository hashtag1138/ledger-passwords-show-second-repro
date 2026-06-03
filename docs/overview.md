# Vue d'ensemble

Ce repo autonome est organisé pour répondre à quatre besoins :

1. builder l'app upstream originale ;
2. builder la même app avec un patch minimal ;
3. reproduire le crash sur `original` ;
4. démontrer que le patch supprime le crash sur `patched`.

## Structure utile

- `repro` : point d'entrée unique
- `repro.lock.json` : commit upstream et images Docker figés
- `cases/regression_cases.json` : scénarios de test
- `patches/app-passwords/` : patch et doc du patch
- `scripts/build.py` : build original + patched
- `scripts/test.py` : repro complète + rapport
- `scripts/speculos_harness.py` : pilotage Speculos et UI Nano
- `artifacts/` : tout le généré

## Variantes construites

- `original` : checkout upstream inchangé
- `patched` : checkout upstream + patch `show second`
