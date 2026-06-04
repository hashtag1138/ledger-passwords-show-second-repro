# `app-passwords` Patch Catalog

This repository applies patches to the upstream `LedgerHQ/app-passwords` checkout selected by [repro.lock.json](../../repro.lock.json).

The catalog driving fix selection is:

- [patches/app-passwords/fix-catalog.json](fix-catalog.json)

## Always-Applied Candidate Patch

Every candidate build also applies:

- [0000-bump-candidate-version-to-1.3.2.patch](0000-bump-candidate-version-to-1.3.2.patch)

Purpose:

- distinguish patched candidates from upstream `1.3.1`
- let the companion require `Passwords >= 1.3.2` before real hardware writes

Doc:

- [docs/bugs/candidate-version-1.3.2.md](../../docs/bugs/candidate-version-1.3.2.md)

## Available Fixes

### `show-second-index`

Patch:

- [0001-fix-show-second-index.patch](0001-fix-show-second-index.patch)

Purpose:

- fix wrong absolute index recomputation in `Passwords list`

Docs:

- [docs/root-cause.md](../../docs/root-cause.md)
- [docs/patch-explained.md](../../docs/patch-explained.md)

### `azerty-right-alt`

Patch:

- [0002-use-right-alt-for-azerty-third-level.patch](0002-use-right-alt-for-azerty-third-level.patch)

Purpose:

- use `Right Alt` / `AltGr` for `AZERTY` third-level HID characters instead of `Left Alt`

Docs:

- [docs/bugs/azerty-right-alt.md](../../docs/bugs/azerty-right-alt.md)
- [docs/plans/azerty-right-alt-implementation-plan.md](../../docs/plans/azerty-right-alt-implementation-plan.md)

## Build Examples

Build only the existing list-index fix:

```bash
./repro build --fixes show-second-index
```

Build only the `AZERTY Right Alt` fix:

```bash
./repro build --fixes azerty-right-alt
```

Build both fixes together:

```bash
./repro build --fixes show-second-index,azerty-right-alt
```

## Real-Device Install Example

```bash
scripts/load-passwords-app-real-device.sh --fixes show-second-index,azerty-right-alt --model nanosp
```
