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

Every candidate build also applies the base version patch documented in [docs/bugs/candidate-version-1.3.2.md](docs/bugs/candidate-version-1.3.2.md).

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

- overview: [docs/overview.md](docs/overview.md)
- reproduction and workflow: [docs/reproduction.md](docs/reproduction.md)
- real-device installation: [docs/install-on-ledger.md](docs/install-on-ledger.md)
- index bug root cause: [docs/root-cause.md](docs/root-cause.md)
- index patch explanation: [docs/patch-explained.md](docs/patch-explained.md)
- UI glyph issue: [docs/bugs/ui-show-glyph.md](docs/bugs/ui-show-glyph.md)
- candidate version bump: [docs/bugs/candidate-version-1.3.2.md](docs/bugs/candidate-version-1.3.2.md)
- `AZERTY Right Alt` bug: [docs/bugs/azerty-right-alt.md](docs/bugs/azerty-right-alt.md)
- `AZERTY Right Alt` implementation plan: [docs/plans/azerty-right-alt-implementation-plan.md](docs/plans/azerty-right-alt-implementation-plan.md)
- patch catalog: [patches/app-passwords/README.md](patches/app-passwords/README.md)
