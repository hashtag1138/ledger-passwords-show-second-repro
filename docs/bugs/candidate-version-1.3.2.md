# Candidate Build Version `1.3.2`

## Summary

All candidate builds produced by this repository apply a base patch that changes the app version from `1.3.1` to `1.3.2`.

This version bump is not a selectable bug fix. It is always applied to patched candidates.

## Why

Without a version bump, the patched app and the buggy upstream app both report `1.3.1`.

That makes it impossible for external tools such as the companion app to distinguish:

- a known-buggy upstream `1.3.1`
- a locally patched build that contains the fixes from this repository

## Policy

This repository therefore reserves:

- upstream bug-compatible app: `1.3.1`
- patched candidate app from this repo: `1.3.2`

The companion app can then require `Passwords >= 1.3.2` before allowing real hardware writes.

## Patch

The always-applied candidate patch is:

- [patches/app-passwords/0000-bump-candidate-version-to-1.3.2.patch](/home/sofian/Sources/ledger-passwords-show-second-repro/patches/app-passwords/0000-bump-candidate-version-to-1.3.2.patch:1)
