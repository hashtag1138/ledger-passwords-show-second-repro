# `AZERTY` `Right Alt` Bug

## Summary

When both the host and the device are configured as `AZERTY`, some characters can still diverge between:

- the password shown on the device
- the password typed through HID

The root cause is the current `AZERTY` third-level HID path in `app-passwords`.

## Affected Character Family

The current `AZERTY` `ALT` subset includes:

```text
# @ [ \ ] ^ ` { | } ~
```

These are the characters most likely to diverge between `show` and `type password` on a French keyboard.

## Root Cause

The current code uses `Left Alt` for those characters.

On the reported French keyboard, the relevant characters are entered with `AltGr`, i.e. the key to the right of the space bar. In HID terms, that is `Right Alt`.

So the app emits the wrong modifier for the `AZERTY` third-level path.

## Consequence

`show` remains logically correct because it displays the generated ASCII string directly.

`type password` can lose or alter the affected characters because the host does not interpret `Left Alt` as the expected `AltGr` behavior for that key family.

## Frozen Product Decision

This repository freezes the following decision:

- fix `AZERTY` only
- use `Right Alt`
- do not add a new settings menu
- do not add a user-facing choice between `Left Alt` and `Right Alt`
- do not change `QWERTY`
- do not change `QWERTY_INTL`

## Patch

The corresponding app patch is:

- [patches/app-passwords/0002-use-right-alt-for-azerty-third-level.patch](../../patches/app-passwords/0002-use-right-alt-for-azerty-third-level.patch)

## Build Commands

Build only the `AZERTY Right Alt` candidate:

```bash
./repro build --fixes azerty-right-alt
```

Build the existing list-index fix plus the `AZERTY Right Alt` fix:

```bash
./repro build --fixes show-second-index,azerty-right-alt
```

## Test Commands

Automated Speculos regression remains centered on the existing `show second` suite:

```bash
./repro test --fixes azerty-right-alt
./repro test --fixes show-second-index,azerty-right-alt
```

This validates that the candidate fixset does not regress the existing list-selection scenarios.

Real HID validation still requires a physical Ledger:

```bash
scripts/load-passwords-app-real-device.sh --fixes azerty-right-alt --model nanosp
```

## Real-Device Validation Targets

Priority characters:

- `]`
- `{`
- `}`
- `\`
- `|`
- `~`
- `@`

## Related Material

- `docs/plans/azerty-right-alt-implementation-plan.md`
- `docs/bugs/ui-show-glyph.md`
- `patches/app-passwords/README.md`
