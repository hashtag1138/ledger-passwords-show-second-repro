# Install on a Real Ledger

This repository can build and load a selected candidate `app-passwords` fixset onto a compatible real Ledger device.

## Purpose

Use this flow for:

- validating candidate fixes outside Speculos
- checking `AZERTY` HID behavior on a real host keyboard
- observing UI-only issues such as the arrow glyph seen in `show`

## Commands

Install the index fix only:

```bash
scripts/load-passwords-app-real-device.sh --fixes show-second-index --model nanosp
```

Install the `AZERTY Right Alt` fix only:

```bash
scripts/load-passwords-app-real-device.sh --fixes azerty-right-alt --model nanosp
```

Install both fixes:

```bash
scripts/load-passwords-app-real-device.sh --fixes show-second-index,azerty-right-alt --model nanosp
```

## What the Script Does

The script:

1. clones the pinned upstream `app-passwords` revision
2. applies the always-on candidate version bump to `1.3.2`
3. applies the selected patch set from `patches/app-passwords/fix-catalog.json`
4. builds a real-device variant without `TESTING=1`
5. loads it onto the Ledger over USB

## Default Build Directory

If `--dir` is not provided, the script uses:

```text
artifacts/build/device-candidate-<fix-slug>/app-passwords
```

Examples:

- `artifacts/build/device-candidate-show-second-index/app-passwords`
- `artifacts/build/device-candidate-azerty-right-alt/app-passwords`
- `artifacts/build/device-candidate-show-second-index__azerty-right-alt/app-passwords`

## Validation Recommendations

After loading:

- for the index fix:
  validate that `show second` no longer crashes
- for the `AZERTY Right Alt` fix:
  validate `]`, `{`, `}`, `\`, `|`, `~`
- for the UI glyph issue:
  compare the `show` rendering against the known logical password where applicable
