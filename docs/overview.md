# Overview

This repository is organized around four complementary goals:

1. build the upstream `app-passwords` baseline;
2. build a candidate variant with a selected fix set;
3. validate the candidate against existing Speculos regressions;
4. document bug analyses, fix decisions, and real-device validation flows.

## Useful Structure

- `repro`: single entry point
- `repro.lock.json`: pinned upstream commit and Docker images
- `cases/regression_cases.json`: current automated Speculos regression cases
- `patches/app-passwords/`: patch catalog and patch files
- `scripts/build.py`: upstream + candidate build
- `scripts/test.py`: Speculos regression + report
- `scripts/load-passwords-app-real-device.sh`: real-device build + load helper
- `scripts/speculos_harness.py`: Speculos and Nano UI automation
- `docs/bugs/`: bug analyses
- `docs/plans/`: implementation plans
- `artifacts/`: generated outputs

## Current Fix IDs

- `show-second-index`
- `azerty-right-alt`

## Current Limitations

- the existing automated suite is still the `show second` regression suite;
- the `azerty-right-alt` fix requires real-device HID validation;
- all candidate builds are version-bumped to `1.3.2` to distinguish them from buggy upstream `1.3.1`;
- the UI arrow glyph issue is documented but not patched yet because the exact rendering root cause is not isolated.
