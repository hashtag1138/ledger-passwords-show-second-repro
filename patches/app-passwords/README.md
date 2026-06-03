# Patch `show second`

## Fichier

- patch : `0001-fix-show-second-index.patch`

## Ce que fait le patch

Le patch corrige la sélection d'un item dans `Passwords list` sur Nano / Speculos.

Avant :

- `password_callback()` recalculait un index absolu avec `page * nbPasswordsPerPage + index`

Après :

- `password_callback()` transmet directement `index`

## Pourquoi

Sur Nano, le callback de `CHOICES_LIST` reçoit déjà l'index absolu de l'item sélectionné. Le recalcul appliquait donc une seconde translation.

Conséquence sur une liste à deux entrées :

- premier item : `0` -> OK
- second item : `2` -> hors borne

Cela suffisait à faire lire un pointeur invalide dans `show_password_cb()`, puis à finir en crash `signal 11`.

## Comment l'appliquer manuellement

Depuis un checkout de `LedgerHQ/app-passwords` au commit figé par `repro.lock.json` :

```bash
git apply patches/app-passwords/0001-fix-show-second-index.patch
```

Le repo applique automatiquement ce patch dans `./repro build`.
