# Reproduction

## Commands

Build:

```bash
./repro build
```

Full reproduction:

```bash
./repro test
```

Install the patched app on a real Ledger:

```bash
scripts/load-passwords-app-real-device.sh --model nanosp
```

## What `./repro build` does

- clones `LedgerHQ/app-passwords` at the pinned commit
- prepares two worktrees under `artifacts/build/`
- applies the patch to the `patched` variant
- compiles both variants with the Ledger builder Docker image

## What `./repro test` does

- launches Speculos on `original`
- runs the reproduction cases
- relaunches Speculos on `patched`
- reruns the same cases
- generates a comparative Markdown + JSON report

## Covered cases

1. control: one identifier pushed via APDU, `show first`
2. main crash: two valid identifiers pushed via APDU, `show second`
3. device-only proof: UI-only creation of two identifiers, `type second`, then `show second`

The automated `device-only` case uses `a` and `b` to stay stable with automatically driven Nano keyboard input. The bug still extends to the real-world `sofian terki` + `abc` scenario, because the root cause is a list-indexing error rather than nickname content.

## Outputs

- Markdown report: `artifacts/reports/latest.md`
- JSON report: `artifacts/reports/latest.json`
- raw Speculos logs: `artifacts/logs/<run-id>/`

## Real-device install

The Speculos reproduction flow and the real-device install flow are intentionally separate.

- `./repro build` builds the pinned reproduction variants used by Speculos.
- `scripts/load-passwords-app-real-device.sh` prepares a separate patched checkout and builds a real-device variant without `TESTING=1`.

See `docs/install-on-ledger.md` for the real-device loading workflow.
