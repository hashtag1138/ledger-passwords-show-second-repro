# Patch explained

## Intent

The patch does not touch the password generation engine, the metadata format, or NBGL rendering. It only fixes the index passed to the selection callback.

## Before

- the app stored `nbPasswordsPerPage`
- at selection time, it recomputed an index with `page * nbPasswordsPerPage + index`

This scheme is valid only if `index` is page-relative. That is not the case here.

## After

- `page` becomes unused
- the app passes `index` directly
- `nbPasswordsPerPage` is no longer needed

## Why this is the right fix level

- the minimal reproducer disappears
- the single-entry control remains OK
- the `device-only` reproduction disappears as well
- the diff is small and local

This makes the patch fast to review upstream.
