# Overview

This autonomous repository is organized around four goals:

1. build the original upstream app;
2. build the same app with a minimal patch;
3. reproduce the crash on `original`;
4. demonstrate that the patch removes the crash on `patched`.

## Useful structure

- `repro`: single entry point
- `repro.lock.json`: pinned upstream commit and Docker images
- `cases/regression_cases.json`: test scenarios
- `patches/app-passwords/`: patch and patch documentation
- `scripts/build.py`: original + patched build
- `scripts/test.py`: full reproduction + report
- `scripts/speculos_harness.py`: Speculos and Nano UI automation
- `artifacts/`: all generated outputs

## Built variants

- `original`: unchanged upstream checkout
- `patched`: upstream checkout + `show second` patch
