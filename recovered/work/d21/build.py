import hashlib
import json
import shutil
import struct
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, 'vendor-python')
import lz4.block

root = Path('work/d21')
prior = Path('work/d20/build/Sage Selector D20')
output = root / 'build/Sage Selector'
archive = Path('outputs/Sage Selector.zip')
old_archive_hash = hashlib.sha256(archive.read_bytes()).hexdigest() if archive.exists() else None

base = (Path('work/d19/d19.bin')).read_bytes()
old_nso = (prior / 'exefs/subsdk4').read_bytes()
assert old_nso[:4] == b'NSO0'
assert hashlib.sha256(base).digest() == old_nso[64:96]
for index in range(3):
    offset, address, size = struct.unpack_from('<III', old_nso, 16 + 16 * index)
    compressed_size = struct.unpack_from('<I', old_nso, 96 + 4 * index)[0]
    data = lz4.block.decompress(old_nso[offset:offset + compressed_size], uncompressed_size=size)
    assert data == base[address:address + size]

raw = bytearray(base)
patches = {
    # Initial auto-skip X press: 3 seconds -> 2 seconds at 19.2 MHz.
    0x3224: (0x529d0009, 0xf000),
    0x3228: (0x72a06dc9, 0x0249),
    # Mounted hold: 350 ms -> 300 ms.
    0x1be18: (0x52914009, 0xe400),
    0x1be20: (0x72a00cc9, 0x0057),
    # On-foot hold uses a threshold-minus-one comparison.
    0x9484: (0xd2913fe1, 0xe3ff),
    0x9488: (0xf2a00cc1, 0x0057),
}
for address, (expected, immediate) in patches.items():
    actual = struct.unpack_from('<I', raw, address)[0]
    assert actual == expected, (hex(address), hex(actual))
    struct.pack_into('<I', raw, address, (actual & ~0x1fffe0) | (immediate << 5))

def imm16(address):
    return (struct.unpack_from('<I', raw, address)[0] >> 5) & 0xffff

assert imm16(0x3224) | (imm16(0x3228) << 16) == 2 * 19200000
assert imm16(0x1be18) | (imm16(0x1be20) << 16) == 300 * 19200
assert imm16(0x9484) | (imm16(0x9488) << 16) == 300 * 19200 - 1
changed_bytes = [i for i, (a, b) in enumerate(zip(base, raw)) if a != b]
assert len(base) == len(raw) and changed_bytes
assert all(any(address <= i < address + 4 for address in patches) for i in changed_bytes)
(root / 'd21.bin').write_bytes(raw)

header = bytearray(old_nso[:256])
body = bytearray()
for index in range(3):
    _, address, size = struct.unpack_from('<III', header, 16 + 16 * index)
    data = raw[address:address + size]
    packed = lz4.block.compress(data, store_size=False, mode='high_compression', compression=12)
    struct.pack_into('<III', header, 16 + 16 * index, 256 + len(body), address, size)
    struct.pack_into('<I', header, 96 + 4 * index, len(packed))
    header[160 + 32 * index:192 + 32 * index] = hashlib.sha256(data).digest()
    body.extend(packed)
header[64:96] = hashlib.sha256(raw).digest()
nso = bytes(header + body)

shutil.copytree(prior, output, dirs_exist_ok=True)
for p in output.glob('*NOTES*'):
    p.unlink()
(output / 'exefs/subsdk4').write_bytes(nso)

changed_files = []
for p in output.rglob('*'):
    if p.is_file():
        name = str(p.relative_to(output))
        if p.read_bytes() != (prior / name).read_bytes():
            changed_files.append(name)
assert changed_files == ['exefs/subsdk4'], changed_files

temporary_archive = archive.with_suffix('.zip.tmp')
with zipfile.ZipFile(temporary_archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for p in sorted(output.rglob('*')):
        if p.is_file():
            z.write(p, str(p.relative_to(output.parent)))
temporary_archive.replace(archive)

with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    assert len(z.namelist()) == 6
    assert all(name.startswith('Sage Selector/') for name in z.namelist())
    assert z.read('Sage Selector/exefs/subsdk4') == nso
    for p in output.rglob('*'):
        if p.is_file():
            name = 'Sage Selector/' + str(p.relative_to(output))
            assert z.read(name) == p.read_bytes()
for index in range(3):
    offset, address, size = struct.unpack_from('<III', nso, 16 + 16 * index)
    compressed_size = struct.unpack_from('<I', nso, 96 + 4 * index)[0]
    data = lz4.block.decompress(nso[offset:offset + compressed_size], uncompressed_size=size)
    assert data == raw[address:address + size]
    assert hashlib.sha256(data).digest() == nso[160 + 32 * index:192 + 32 * index]

new_archive_hash = hashlib.sha256(archive.read_bytes()).hexdigest()
assert new_archive_hash != old_archive_hash
(root / 'verification.json').write_text(json.dumps({
    'previous_clean_zip_sha256': old_archive_hash,
    'new_clean_zip_sha256': new_archive_hash,
    'changed_game_files_vs_D20': changed_files,
    'changed_raw_instruction_addresses': [hex(x) for x in sorted(patches)],
    'mounted_and_on_foot_hold_ms': 300,
    'memory_initial_auto_skip_seconds': 2,
    'memory_icon_identical_to_D20': True,
}, indent=2) + '\n')
print(archive, archive.stat().st_size, 'bytes', new_archive_hash)
