#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOCK_FILE="${ROOT_DIR}/repro.lock.json"
APP_DIR_DEFAULT="${ROOT_DIR}/artifacts/build/device-patched/app-passwords"
PATCH_FILE_DEFAULT="${ROOT_DIR}/patches/app-passwords/0001-fix-show-second-index.patch"

APP_DIR="${APP_PASSWORDS_DIR:-$APP_DIR_DEFAULT}"
PATCH_FILE="${APP_PASSWORDS_PATCH_FILE:-$PATCH_FILE_DEFAULT}"
REPO_URL=""
COMMIT=""
IMAGE=""
MODEL="${LEDGER_DEVICE_MODEL:-nanosp}"
DOCKER_PREFIX=()
FORCE=0
RUN_BUILD=1

usage() {
    cat <<'EOF'
Usage:
  scripts/load-passwords-app-real-device.sh [options]

Options:
  --dir PATH         app-passwords checkout/build directory.
                     Default: artifacts/build/device-patched/app-passwords
  --model MODEL      Target Ledger model. Default: nanosp
                     Supported: nanos, nanosp, stax, flex
  --patch PATH       Patch file to apply before building.
                     Default: patches/app-passwords/0001-fix-show-second-index.patch
  --no-build         Skip the build step and run only the load step.
  --sudo-docker      Prefix Docker commands with sudo.
  --force            Continue despite non-fatal safety checks.
  --help             Show this help.

Notes:
  - This script targets a real Ledger device, not Speculos.
  - The device must be connected over USB, unlocked, and left on the dashboard.
  - Side-loading custom apps is not supported on Nano X.
  - Ledger Live should be closed before running this script.
  - This script uses the pinned upstream commit and builder image from repro.lock.json.
  - The real-device build is separate from ./repro build and does not use TESTING=1.
EOF
}

while (($# > 0)); do
    case "$1" in
        --dir)
            APP_DIR="${2:-}"
            shift 2
            ;;
        --model)
            MODEL="${2:-}"
            shift 2
            ;;
        --patch)
            PATCH_FILE="${2:-}"
            shift 2
            ;;
        --no-build)
            RUN_BUILD=0
            shift
            ;;
        --sudo-docker)
            DOCKER_PREFIX=(sudo)
            shift
            ;;
        --force)
            FORCE=1
            shift
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            usage >&2
            exit 1
            ;;
    esac
done

APP_DIR="$(mkdir -p "$APP_DIR" && cd "$APP_DIR" && pwd)"
PATCH_FILE="$(cd "$(dirname "$PATCH_FILE")" && pwd)/$(basename "$PATCH_FILE")"

timestamp() {
    date '+%Y-%m-%d %H:%M:%S'
}

section() {
    printf '\n[%s] %s\n' "$(timestamp)" "$1"
}

info() {
    printf '[INFO] %s\n' "$1"
}

warn() {
    printf '[WARN] %s\n' "$1" >&2
}

fail() {
    printf '[ERROR] %s\n' "$1" >&2
    exit 1
}

quote_cmd() {
    local quoted=""
    printf -v quoted '%q ' "$@"
    printf '%s' "${quoted% }"
}

run_cmd() {
    info "+ $(quote_cmd "$@")"
    "$@"
}

read_lock_value() {
    local python_expr="$1"
    python3 - "$LOCK_FILE" "$python_expr" <<'PY'
import json
import sys
from pathlib import Path

lock_path = Path(sys.argv[1])
expr = sys.argv[2]
data = json.loads(lock_path.read_text(encoding="utf-8"))
value = eval(expr, {"__builtins__": {}}, {"data": data})
if not isinstance(value, str):
    raise SystemExit(f"Expected a string for {expr!r}, got {type(value).__name__}")
print(value)
PY
}

model_to_sdk_env() {
    case "$1" in
        nanos)
            printf '%s' "NANOS_SDK"
            ;;
        nanosp)
            printf '%s' "NANOSP_SDK"
            ;;
        stax)
            printf '%s' "STAX_SDK"
            ;;
        flex)
            printf '%s' "FLEX_SDK"
            ;;
        nanox)
            fail "Nano X does not support app side-loading with this flow. Use a Nano S, Nano S+, Stax, or Flex."
            ;;
        *)
            fail "Unsupported model: $1"
            ;;
    esac
}

ensure_prereqs() {
    section "Prerequisite checks"
    command -v git >/dev/null 2>&1 || fail "git is required"
    command -v docker >/dev/null 2>&1 || fail "docker is required"
    command -v python3 >/dev/null 2>&1 || fail "python3 is required"
    [[ -f "$LOCK_FILE" ]] || fail "Missing lock file: $LOCK_FILE"
    [[ -f "$PATCH_FILE" ]] || fail "Patch file not found: $PATCH_FILE"
    run_cmd "${DOCKER_PREFIX[@]}" docker version >/dev/null

    REPO_URL="$(read_lock_value "data['app_passwords']['repo']")"
    COMMIT="$(read_lock_value "data['app_passwords']['commit']")"
    IMAGE="$(read_lock_value "data['docker_images']['builder']")"

    info "Root dir: $ROOT_DIR"
    info "Lock file: $LOCK_FILE"
    info "App dir: $APP_DIR"
    info "Patch file: $PATCH_FILE"
    info "Pinned repo: $REPO_URL"
    info "Pinned commit: $COMMIT"
    info "Docker image: $IMAGE"
    info "Target model: $MODEL"
}

prepare_checkout() {
    section "Preparing patched checkout"
    if [[ ! -d "$APP_DIR/.git" ]]; then
        info "No checkout found, cloning app-passwords"
        rm -rf "$APP_DIR"
        run_cmd git clone "$REPO_URL" "$APP_DIR"
    fi

    run_cmd git -C "$APP_DIR" fetch --tags origin
    run_cmd git -C "$APP_DIR" checkout --force "$COMMIT"
    run_cmd git -C "$APP_DIR" clean -fdx
    run_cmd git -C "$APP_DIR" apply "$PATCH_FILE"

    info "Git HEAD: $(git -C "$APP_DIR" rev-parse --short HEAD)"
    info "Patch applied from: $PATCH_FILE"
}

detect_ledger_usb() {
    section "USB device detection"
    if [[ ! -d /dev/bus/usb ]]; then
        warn "/dev/bus/usb is not present on this host"
    else
        info "USB bus directory is present"
    fi

    if command -v lsusb >/dev/null 2>&1; then
        local devices
        devices="$(lsusb -d 2c97: 2>/dev/null || true)"
        if [[ -n "$devices" ]]; then
            info "Ledger USB device(s) detected:"
            printf '%s\n' "$devices"
        else
            warn "No Ledger USB device detected with lsusb vendor id 2c97"
            warn "Check cable, unlock the Ledger, and leave it on the dashboard"
            if ((FORCE)); then
                warn "Continuing because --force was provided"
            else
                fail "Ledger device not detected"
            fi
        fi
    else
        warn "lsusb is not installed, skipping USB vendor detection"
    fi

    if pgrep -af 'Ledger Live|ledger-live' >/dev/null 2>&1; then
        warn "A Ledger Live process appears to be running"
        warn "Close Ledger Live before loading a custom app"
    else
        info "No Ledger Live process detected"
    fi
}

print_app_debug() {
    section "App metadata"
    local makefile="$APP_DIR/Makefile"
    if [[ -f "$makefile" ]]; then
        local version_major version_minor version_patch
        version_major="$(awk -F= '/^APPVERSION_M=/{gsub(/[[:space:]]/,"",$2); print $2}' "$makefile" | tail -n1)"
        version_minor="$(awk -F= '/^APPVERSION_N=/{gsub(/[[:space:]]/,"",$2); print $2}' "$makefile" | tail -n1)"
        version_patch="$(awk -F= '/^APPVERSION_P=/{gsub(/[[:space:]]/,"",$2); print $2}' "$makefile" | tail -n1)"
        if [[ -n "$version_major" && -n "$version_minor" && -n "$version_patch" ]]; then
            info "App version: ${version_major}.${version_minor}.${version_patch}"
        fi
    fi

    if grep -q 'selector_callback(index);' "$APP_DIR/src/ui/ui_passwords.c"; then
        info "Patched callback pattern detected in src/ui/ui_passwords.c"
    else
        warn "Patched callback pattern not found in src/ui/ui_passwords.c"
        if ((FORCE)); then
            warn "Continuing because --force was provided"
        else
            fail "Patched callback pattern not detected"
        fi
    fi
}

docker_tty_args() {
    if [[ -t 0 && -t 1 ]]; then
        printf '%s\n' "-ti"
    fi
}

build_app() {
    local sdk_env="$1"
    section "Building app for real device"
    local tty_arg=""
    tty_arg="$(docker_tty_args || true)"
    local -a cmd=("${DOCKER_PREFIX[@]}" docker run --rm)
    if [[ -n "$tty_arg" ]]; then
        cmd+=("$tty_arg")
    fi
    cmd+=(
        --user "$(id -u):$(id -g)"
        -v "$APP_DIR:/app"
        -w /app
        "$IMAGE"
        bash -lc "BOLOS_SDK=\$${sdk_env} make clean && BOLOS_SDK=\$${sdk_env} make all"
    )
    run_cmd "${cmd[@]}"

    [[ -f "$APP_DIR/bin/app.elf" ]] || fail "Missing build artifact: $APP_DIR/bin/app.elf"
    [[ -f "$APP_DIR/bin/app.apdu" ]] || fail "Missing build artifact: $APP_DIR/bin/app.apdu"

    info "Build artifacts:"
    ls -lh "$APP_DIR/bin/app.elf" "$APP_DIR/bin/app.apdu" "$APP_DIR/bin/app.hex" 2>/dev/null || true
    if [[ -f "$APP_DIR/bin/app.sha256" ]]; then
        info "app.sha256: $(cat "$APP_DIR/bin/app.sha256")"
    fi
}

load_app() {
    local sdk_env="$1"
    section "Loading app onto Ledger"
    info "Expected device state:"
    info "- connected over USB"
    info "- unlocked"
    info "- on the dashboard, not inside an app"
    info "- Ledger Live closed"

    local tty_arg=""
    tty_arg="$(docker_tty_args || true)"
    local -a cmd=("${DOCKER_PREFIX[@]}" docker run --rm)
    if [[ -n "$tty_arg" ]]; then
        cmd+=("$tty_arg")
    fi
    # Real USB device nodes are commonly root-owned, so the load step runs as
    # root inside the container even though the build step runs as the host uid.
    cmd+=(
        --privileged
        -v /dev/bus/usb:/dev/bus/usb
        -v "$APP_DIR:/app"
        -w /app
        "$IMAGE"
        bash -lc "BOLOS_SDK=\$${sdk_env} make load"
    )
    run_cmd "${cmd[@]}"
}

main() {
    local sdk_env
    sdk_env="$(model_to_sdk_env "$MODEL")"

    ensure_prereqs
    prepare_checkout
    detect_ledger_usb
    print_app_debug

    if ((RUN_BUILD)); then
        build_app "$sdk_env"
    else
        section "Skipping build"
        info "Using existing binaries under $APP_DIR/bin"
    fi

    load_app "$sdk_env"

    section "Done"
    info "If the load succeeded, the patched Passwords app is now installed on the Ledger."
    info "Next step: open Passwords on the device and validate the fixed scenario."
}

main "$@"
