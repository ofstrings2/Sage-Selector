# Source recovery status

This is a source recovery and attribution publication for Sage Selector D28 on
TotK 1.2.1. It is not a claim that the combined binary is GPL compliant.

- `recovered/work/`: all recovered editable top-level and D07–D28 Python, C and
  assembly source, including historical experiments and host tests. Some files
  are superseded and are retained to document how this binary was developed.
- `vendor/EmoteWheel/`: unmodified public source snapshot `26c94741abe3932b2ff6d7d38e9e8d924b445249`,
  with original per-file licenses and notices preserved.
- `config/`: D28 JSON configuration, byte-identical to the recovered final build.
- `licenses/`: GPLv3, GPLv2, ISC and MIT notices and original upstream notices.
- `evidence/`: exact file hashes, source provenance and license inventory.

Development scripts originally used absolute local paths. Those paths have been
normalized to external `inputs/` locations; no gameplay logic has been edited.
Each original and normalized source hash is recorded in `evidence/recovered-source.json`.

The historical scripts are not a verified end-to-end build. They refer to prior
generated stage images, native game files and a supplied fixed D10 binary whose
complete build source has not been recovered. The newly published upstream
source has not been matched to the exact donor by a rebuild. Do not substitute
this archive for verified complete corresponding source when distributing GPL
object code. See RELEASE_BLOCKERS.md and BUILDING.md for the remaining work.

Source project URL: https://github.com/ofstrings2/Sage-Selector
This URL is a publication destination, not proof that publication is complete.
