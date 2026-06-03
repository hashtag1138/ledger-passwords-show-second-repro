# Cause racine

## Verdict

Le crash `show second` vient de `app-passwords`, pas du companion.

## Point causal

Le bug est dans `src/ui/ui_passwords.c`, dans `password_callback()`.

Le callback faisait :

```c
selector_callback((page * nbPasswordsPerPage) + index);
```

Sur Nano / Speculos, pour cette `CHOICES_LIST`, `index` est déjà absolu. La translation était donc appliquée deux fois.

## Effet

Pour une liste à deux entrées :

- premier item : `index = 0`, le calcul reste `0`
- second item : `index = 1`, le calcul devient `2`

L'app lit alors hors de la liste logique, ce qui suffit à casser `show_password_cb()` sur le second item.

## Pourquoi le companion n'est pas requis

La repro `device-only` du repo montre que le crash apparaît aussi sans aucune interaction avec le companion :

- création de deux entrées via l'UI du Ledger
- `type` du second : OK
- `show` du second : crash sur `original`

Le companion ne faisait que pousser un état valide que l'app device gérait mal ensuite.
