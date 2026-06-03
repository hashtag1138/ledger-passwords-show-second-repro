# `show second` patch

## File

- patch: `0001-fix-show-second-index.patch`

## What the patch does

The patch fixes item selection in `Passwords list` on Nano / Speculos.

Before:

- `password_callback()` recomputed an absolute index with `page * nbPasswordsPerPage + index`

After:

- `password_callback()` passes `index` directly

## Why

On Nano, the `CHOICES_LIST` callback already receives the absolute index of the selected item. The recomputation therefore applied a second translation.

Effect on a two-entry list:

- first item: `0` -> OK
- second item: `2` -> out of bounds

That was enough to make `show_password_cb()` read an invalid pointer and eventually crash with `signal 11`.

## How to apply it manually

From a `LedgerHQ/app-passwords` checkout at the commit pinned by `repro.lock.json`:

```bash
git apply patches/app-passwords/0001-fix-show-second-index.patch
```

The repository applies this patch automatically in `./repro build`.
