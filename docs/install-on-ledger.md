# Install The Patched Build On A Real Ledger

## Scope

This repository is primarily built around Speculos reproduction, but it can also build and load the patched `Passwords` app onto a compatible real Ledger device.

This flow is meant for:

- validating the fix on hardware;
- checking that the patched app still opens and behaves normally on device;
- reproducing the original real-world scenario after installing the patched build.

It is not meant for routine everyday use.

## Supported devices

The helper supports the same side-loading flow as Ledger's standard developer tooling:

- `nanos`
- `nanosp`
- `stax`
- `flex`

`Nano X` is intentionally rejected by the script because this side-loading flow is not supported there.

## Important warnings

- Back up your current vault before replacing the app.
- Close Ledger Live before loading the custom app.
- Leave the Ledger unlocked and on the dashboard.
- Treat this as a custom developer build, not as a production-supported installation path.

## Command

For a Nano S Plus:

```bash
scripts/load-passwords-app-real-device.sh --model nanosp
```

Useful variants:

```bash
scripts/load-passwords-app-real-device.sh --model nanosp --sudo-docker
scripts/load-passwords-app-real-device.sh --model nanosp --no-build
scripts/load-passwords-app-real-device.sh --model nanosp --force
```

## What the script does

The helper:

1. reads the pinned upstream repo, commit, and builder image from `repro.lock.json`;
2. prepares a fresh checkout under `artifacts/build/device-patched/app-passwords`;
3. applies `patches/app-passwords/0001-fix-show-second-index.patch`;
4. prints debug information such as:
   - checkout path
   - pinned commit
   - target model
   - detected app version
   - whether a Ledger USB device was found
   - whether Ledger Live seems to be running
5. builds a real-device app variant without `TESTING=1`;
6. runs `make load` through Ledger's official builder image.

## Debug output you should expect

When things are healthy, the script should explicitly show:

- the Ledger USB device detected through `lsusb -d 2c97:`
- the pinned app version from `Makefile`
- the patched callback pattern found in `src/ui/ui_passwords.c`
- the generated artifacts in `bin/`
- the final `make load` command

If the device is not detected, the script stops unless you pass `--force`.

## After installation

Once the load succeeds:

1. open the `Passwords` app on the device;
2. validate the safe control path first;
3. then retry the failing scenario on hardware.

The expected outcome after the patch is:

- `show first` still works;
- `show second` no longer crashes after a two-entry state;
- the UI-only two-entry scenario no longer crashes either.
