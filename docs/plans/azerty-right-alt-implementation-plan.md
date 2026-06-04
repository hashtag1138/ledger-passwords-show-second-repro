# `AZERTY Right Alt` Implementation Plan

## Frozen Decision

The implementation is constrained as follows:

- apply the fix to `AZERTY` only
- use `Right Alt` / `AltGr`
- do not introduce any new menu or persistent configuration
- preserve `QWERTY`
- preserve `QWERTY_INTL`

## Scope

In scope:

- `src/hid_mapping.c`
- `src/hid_mapping.h`
- `tests/unit/test_hid_mapping.c`
- repository build/test/install tooling for selecting this patch

Out of scope:

- UI glyph rendering fix
- companion-side changes
- APDU config changes
- any new settings screen

## Patch Direction

The patch must:

1. preserve the current character table for `AZERTY`
2. preserve the current `QWERTY` behavior
3. preserve the current `QWERTY_INTL` behavior
4. change only the modifier emitted for `AZERTY` third-level characters

## Validation Strategy

### Automated

The automated Speculos suite in this repo still focuses on the `show second` regression.

It is used here as a non-regression suite:

- building `azerty-right-alt` alone must not regress the existing upstream behavior unrelated to list selection
- building `show-second-index,azerty-right-alt` must still pass the original crash fix expectations

### Manual

The real correctness check for this patch is on a physical Ledger with an `AZERTY` host keyboard.

Priority validation set:

- `]`
- `{`
- `}`
- `\`
- `|`
- `~`

## Commands

Build:

```bash
./repro build --fixes azerty-right-alt
./repro build --fixes show-second-index,azerty-right-alt
```

Speculos non-regression:

```bash
./repro test --fixes azerty-right-alt
./repro test --fixes show-second-index,azerty-right-alt
```

Real-device install:

```bash
scripts/load-passwords-app-real-device.sh --fixes azerty-right-alt --model nanosp
scripts/load-passwords-app-real-device.sh --fixes show-second-index,azerty-right-alt --model nanosp
```

## Acceptance Criteria

The patch is acceptable when:

1. `AZERTY` third-level characters use `Right Alt`
2. no new menu is added
3. `QWERTY` and `QWERTY_INTL` remain unchanged
4. unit coverage is expanded for the `AZERTY` third-level subset
5. real-device validation confirms that characters such as `]` no longer disappear on `AZERTY/AZERTY`
