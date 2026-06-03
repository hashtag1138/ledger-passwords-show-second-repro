# Root cause

## Verdict

The `show second` crash comes from `app-passwords`, not from the companion.

## Causal point

The bug is in `src/ui/ui_passwords.c`, inside `password_callback()`.

The callback used to do:

```c
selector_callback((page * nbPasswordsPerPage) + index);
```

On Nano / Speculos, for this `CHOICES_LIST`, `index` is already absolute. The translation was therefore applied twice.

## Effect

For a two-entry list:

- first item: `index = 0`, the calculation remains `0`
- second item: `index = 1`, the calculation becomes `2`

The app then reads outside the logical list, which is enough to break `show_password_cb()` on the second item.

## Why the companion is not required

The repository's `device-only` reproduction shows that the crash also appears without any interaction with the companion:

- creation of two entries through the Ledger UI
- `type` on the second: OK
- `show` on the second: crash on `original`

The companion was only pushing a valid state that the device app mishandled afterwards.
