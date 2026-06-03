# Patch expliqué

## Intention

Le patch ne touche ni au moteur de génération de mot de passe, ni au format des metadata, ni au rendu NBGL. Il corrige uniquement l'index transmis au callback de sélection.

## Avant

- l'app stockait `nbPasswordsPerPage`
- au moment de la sélection, elle recalculait un index avec `page * nbPasswordsPerPage + index`

Ce schéma est valide seulement si `index` est relatif à la page. Ce n'est pas le cas ici.

## Après

- `page` devient inutilisé
- l'app transmet directement `index`
- `nbPasswordsPerPage` n'est plus nécessaire

## Pourquoi c'est le bon niveau de fix

- le reproducer minimal disparaît
- le contrôle mono-entrée reste OK
- la repro `device-only` disparaît aussi
- le diff est petit et local

Le patch est donc reviewable rapidement côté upstream.
