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

Use `--sudo-docker` only when your user cannot talk to the Docker daemon itself.
It is not the fix for the usual Ledger USB permission issue inside the container.

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

## Docker and USB permission troubleshooting

The most common failure mode is:

```text
OSError: open failed
```

coming from `ledgerblue.loadApp` during `make load`.

### Why this happens

On many Linux hosts, the Ledger USB node under `/dev/bus/usb/...` is owned by `root`, for example:

```text
crw-rw-r-- 1 root root ... /dev/bus/usb/001/015
```

In that setup, a container process running as your host uid often cannot open the HID device even if:

- Docker itself works correctly;
- `lsusb` detects the Ledger;
- the build phase succeeds.

### What this repository does about it

The helper intentionally splits the two phases:

- the build phase runs as your host uid so generated files are not owned by `root`;
- the `make load` phase runs as `root` inside the container so `ledgerblue` can open the real USB device.

That is why the script can succeed even when manual Docker invocations fail with `open failed`.

### When to use `--sudo-docker`

Use:

```bash
scripts/load-passwords-app-real-device.sh --model nanosp --sudo-docker
```

only if Docker itself is inaccessible, for example when:

- `docker version` fails with a daemon permission error;
- your user is not allowed to access the Docker socket.

`--sudo-docker` is about Docker daemon access.
It is separate from the USB HID permission problem handled by running `make load` as root inside the container.

### If `open failed` still appears

Check these points in order:

1. make sure Ledger Live is fully closed;
2. keep the Ledger unlocked and on the dashboard;
3. unplug and replug the Ledger, then rerun the script;
4. rerun once with `--sudo-docker` if Docker access itself is flaky;
5. confirm the Ledger is still visible with `lsusb -d 2c97:`.

If the script says the Ledger is detected but `ledgerblue` still cannot open it, the issue is almost always host USB access contention or host policy around HID device access.

### Running outside Docker

If you later try to load the app without this helper and without Docker, you may need proper udev rules on the host so non-root processes can access the Ledger HID device.
This repository does not manage host udev setup; it works around the common case by running the load step as root inside the container.

## After installation

Once the load succeeds:

1. open the `Passwords` app on the device;
2. validate the safe control path first;
3. then retry the failing scenario on hardware.

The expected outcome after the patch is:

- `show first` still works;
- `show second` no longer crashes after a two-entry state;
- the UI-only two-entry scenario no longer crashes either.
