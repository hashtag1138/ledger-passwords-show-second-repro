# ledger-passwords-show-second-repro

Companion repository: [`hashtag1138/ledger-password-companion-app`](https://github.com/hashtag1138/ledger-password-companion-app)

Autonomous repository to reproduce, document, and validate the `show second` crash fix in `LedgerHQ/app-passwords`.

## Goal

This repository:

- clones `LedgerHQ/app-passwords` at a pinned commit;
- builds an `original` variant and a `patched` variant;
- launches Speculos;
- runs `push-style` and `device-only` reproduction scenarios;
- generates a single report comparing `original` vs `patched`.

The repository does not depend on the current companion app to push metadata: the tests speak APDU directly to Speculos, which keeps the reproduction simple and self-contained.

## Prerequisites

- `git`
- `docker`
- `python3` >= `3.11`

## Commands

Build:

```bash
./repro build
```

Full test run:

```bash
./repro test
```

Build + test:

```bash
./repro all
```

Install the patched app on a real Ledger:

```bash
scripts/load-passwords-app-real-device.sh --model nanosp
```

See the full install guide: [`docs/install-on-ledger.md`](docs/install-on-ledger.md)

## Outputs

- original build: `artifacts/build/original/app-passwords/bin/app.elf`
- patched build: `artifacts/build/patched/app-passwords/bin/app.elf`
- build manifest: `artifacts/build/manifest.json`
- latest report: `artifacts/reports/latest.md`
- latest JSON report: `artifacts/reports/latest.json`
- Speculos logs: `artifacts/logs/<run-id>/`

## Documentation

- overview: [`docs/overview.md`](docs/overview.md)
- reproduction: [`docs/reproduction.md`](docs/reproduction.md)
- real-device installation: [`docs/install-on-ledger.md`](docs/install-on-ledger.md)
- root cause: [`docs/root-cause.md`](docs/root-cause.md)
- patch explained: [`docs/patch-explained.md`](docs/patch-explained.md)
- ready-to-apply patch: [`patches/app-passwords/0001-fix-show-second-index.patch`](patches/app-passwords/0001-fix-show-second-index.patch)
