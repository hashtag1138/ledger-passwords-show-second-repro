# Reproduction and Workflow

## Build a Candidate Fixset

Build upstream plus the selected candidate variant:

```bash
./repro build --fixes show-second-index
./repro build --fixes azerty-right-alt
./repro build --fixes show-second-index,azerty-right-alt
```

Candidate builds always include the base version bump to `Passwords 1.3.2`.

The build manifest is written to:

```text
artifacts/build/manifest.json
```

## Run the Existing Speculos Regression Suite

```bash
./repro test --fixes show-second-index
./repro test --fixes azerty-right-alt
./repro test --fixes show-second-index,azerty-right-alt
```

What this currently covers:

- the existing `show second` crash regression
- non-regression of list-selection behavior when other fixes are applied

What it does not currently prove:

- real HID output for the `azerty-right-alt` fix
- the UI arrow glyph rendering anomaly

## Real-Device Validation

Install a candidate build on a real Ledger:

```bash
scripts/load-passwords-app-real-device.sh --fixes show-second-index --model nanosp
scripts/load-passwords-app-real-device.sh --fixes azerty-right-alt --model nanosp
scripts/load-passwords-app-real-device.sh --fixes show-second-index,azerty-right-alt --model nanosp
```

Use the physical device for:

- `AZERTY` HID validation
- `show` glyph observation

## Current Bug Documentation

- index bug:
  - `docs/root-cause.md`
  - `docs/patch-explained.md`
- UI glyph issue:
  - `docs/bugs/ui-show-glyph.md`
- `AZERTY Right Alt` issue:
  - `docs/bugs/azerty-right-alt.md`
  - `docs/plans/azerty-right-alt-implementation-plan.md`
