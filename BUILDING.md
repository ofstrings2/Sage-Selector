# Build status and prerequisites

There is no verified standalone build of the exact D28 release in this recovery.
Do not run all historical scripts as a build pipeline: they include superseded
experiments and depend on generated inputs that are intentionally not published.

## Published upstream framework

The separate vendor/EmoteWheel source snapshot includes BUILDING.txt. It requires
devkitPro/devkitA64, libnx, switch-tools, GNU make and Python. Follow those upstream
instructions to build that snapshot. This does not automatically create Sage
Selector, and its output has not been matched against the historical donor.

## Recovered Sage Selector changes

The relevant files are indexed in SOURCE_INDEX.md. C/assembly payloads used
LLVM/Clang targeting aarch64-none-elf; historical Python linkers placed them at
fixed module addresses and updated branches, NSO metadata and configuration.
Python tools used lz4, capstone, zstandard, Pillow and texture2ddecoder; the later
icon pipeline used astcenc with ASTC 4x4. Those tools are not redistributed here.

The D11 baseline came from an externally supplied fixed D10 ZIP. Its source and
exact source-to-donor toolchain match must be recovered. The D21 runtime then
remained unchanged through D28 while icons/configuration were updated.

To make a releasable source build: obtain the exact donor source/toolchain and
D10 changes, resolve the framework license compatibility, integrate the recovered
changes into an explicit build, then rebuild and validate against the manifest.
Only use locally and lawfully supplied native game files for asset generation;
do not commit them. inputs/, generated stage binaries, and release binaries are
excluded from this source repository.

The hash/packaging check is a local preservation check, not gameplay testing or
proof that all corresponding-source obligations have been met.
