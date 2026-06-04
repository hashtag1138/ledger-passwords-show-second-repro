# ledger-passwords-show-second-repro

Companion repository: [`hashtag1138/ledger-password-companion-app`](https://github.com/hashtag1138/ledger-password-companion-app)

Autonomous repository to reproduce, document, build, and validate targeted fixes for `LedgerHQ/app-passwords`.

## Goal

This repository:

- clones `LedgerHQ/app-passwords` at a pinned commit;
- builds an `upstream` baseline and a `candidate` fixset variant;
- bumps every candidate build to `Passwords 1.3.2` so patched apps can be identified reliably;
- lets you choose which fix set to apply at build time;
- runs the existing Speculos regression suite;
- provides a real-device build + load helper;
- stores bug analysis, fix plans, and patch files in one place.

## Implemented Fix Selection

Current fix ids:

- `show-second-index`
- `azerty-right-alt`

Every candidate build also applies the base version patch documented in [docs/bugs/candidate-version-1.3.2.md](/home/sofian/Sources/ledger-passwords-show-second-repro/docs/bugs/candidate-version-1.3.2.md:1).

Examples:

```bash
./repro build --fixes show-second-index
./repro build --fixes azerty-right-alt
./repro build --fixes show-second-index,azerty-right-alt
```

## Commands

Build:

```bash
./repro build --fixes show-second-index
```

Automated Speculos regression:

```bash
./repro test --fixes show-second-index
```

Build + test:

```bash
./repro all --fixes show-second-index,azerty-right-alt
```

Install a candidate build on a real Ledger:

```bash
scripts/load-passwords-app-real-device.sh --fixes azerty-right-alt --model nanosp
```

## Outputs

- upstream build: `artifacts/build/upstream/app-passwords/bin/app.elf`
- candidate build: `artifacts/build/candidate-<fix-slug>/app-passwords/bin/app.elf`
- build manifest: `artifacts/build/manifest.json`
- latest report: `artifacts/reports/latest.md`
- latest JSON report: `artifacts/reports/latest.json`
- Speculos logs: `artifacts/logs/<run-id>/`

## Documentation

- overview: [docs/overview.md](/home/sofian/Sources/ledger-passwords-show-second-repro/docs/overview.md:1)
- reproduction and workflow: [docs/reproduction.md](/home/sofian/Sources/ledger-passwords-show-second-repro/docs/reproduction.md:1)
- real-device installation: [docs/install-on-ledger.md](/home/sofian/Sources/ledger-passwords-show-second-repro/docs/install-on-ledger.md:1)
- index bug root cause: [docs/root-cause.md](/home/sofian/Sources/ledger-passwords-show-second-repro/docs/root-cause.md:1)
- index patch explanation: [docs/patch-explained.md](/home/sofian/Sources/ledger-passwords-show-second-repro/docs/patch-explained.md:1)
- UI glyph issue: [docs/bugs/ui-show-glyph.md](/home/sofian/Sources/ledger-passwords-show-second-repro/docs/bugs/ui-show-glyph.md:1)
- candidate version bump: [docs/bugs/candidate-version-1.3.2.md](/home/sofian/Sources/ledger-passwords-show-second-repro/docs/bugs/candidate-version-1.3.2.md:1)
- `AZERTY Right Alt` bug: [docs/bugs/azerty-right-alt.md](/home/sofian/Sources/ledger-passwords-show-second-repro/docs/bugs/azerty-right-alt.md:1)
- `AZERTY Right Alt` implementation plan: [docs/plans/azerty-right-alt-implementation-plan.md](/home/sofian/Sources/ledger-passwords-show-second-repro/docs/plans/azerty-right-alt-implementation-plan.md:1)
- patch catalog: [patches/app-passwords/README.md](/home/sofian/Sources/ledger-passwords-show-second-repro/patches/app-passwords/README.md:1)
