# `app-passwords` Patch Catalog

This repository applies patches to the upstream `LedgerHQ/app-passwords` checkout selected by [repro.lock.json](/home/sofian/Sources/ledger-passwords-show-second-repro/repro.lock.json:1).

The catalog driving fix selection is:

- [patches/app-passwords/fix-catalog.json](/home/sofian/Sources/ledger-passwords-show-second-repro/patches/app-passwords/fix-catalog.json:1)

## Always-Applied Candidate Patch

Every candidate build also applies:

- [0000-bump-candidate-version-to-1.3.2.patch](/home/sofian/Sources/ledger-passwords-show-second-repro/patches/app-passwords/0000-bump-candidate-version-to-1.3.2.patch:1)

Purpose:

- distinguish patched candidates from upstream `1.3.1`
- let the companion require `Passwords >= 1.3.2` before real hardware writes

Doc:

- [docs/bugs/candidate-version-1.3.2.md](/home/sofian/Sources/ledger-passwords-show-second-repro/docs/bugs/candidate-version-1.3.2.md:1)

## Available Fixes

### `show-second-index`

Patch:

- [0001-fix-show-second-index.patch](/home/sofian/Sources/ledger-passwords-show-second-repro/patches/app-passwords/0001-fix-show-second-index.patch:1)

Purpose:

- fix wrong absolute index recomputation in `Passwords list`

Docs:

- [docs/root-cause.md](/home/sofian/Sources/ledger-passwords-show-second-repro/docs/root-cause.md:1)
- [docs/patch-explained.md](/home/sofian/Sources/ledger-passwords-show-second-repro/docs/patch-explained.md:1)

### `azerty-right-alt`

Patch:

- [0002-use-right-alt-for-azerty-third-level.patch](/home/sofian/Sources/ledger-passwords-show-second-repro/patches/app-passwords/0002-use-right-alt-for-azerty-third-level.patch:1)

Purpose:

- use `Right Alt` / `AltGr` for `AZERTY` third-level HID characters instead of `Left Alt`

Docs:

- [docs/bugs/azerty-right-alt.md](/home/sofian/Sources/ledger-passwords-show-second-repro/docs/bugs/azerty-right-alt.md:1)
- [docs/plans/azerty-right-alt-implementation-plan.md](/home/sofian/Sources/ledger-passwords-show-second-repro/docs/plans/azerty-right-alt-implementation-plan.md:1)

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
