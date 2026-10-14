import hashlib
import json
import shutil
import struct
import sys
import zipfile
import zlib
from pathlib import Path

sys.path.insert(0, 'vendor-python')
sys.path.insert(0, 'tools')
sys.path.insert(0, 'work/d11/vendor')
import zstandard as zstd
import texture2ddecoder
from PIL import Image
from pack_utils import sarc

work = Path('work/d22')
base_mod = Path('work/d21/build/Sage Selector')
mod = work / 'build/Sage Selector'
output = Path('outputs/D22/Sage Selector.zip')
romfs = Path('inputs/romfs')
shutil.copytree(base_mod, mod, dirs_exist_ok=True)

# Decode Nintendo's UI archive using the dictionary from this game dump.
dictionary_pack = zstd.ZstdDecompressor().decompress((romfs / 'Pack/ZsDic.pack.zs').read_bytes())
dictionary_files = sarc(dictionary_pack)
dictionaries = {}
for value in dictionary_files.values():
    dictionary = zstd.ZstdCompressionDict(value)
    dictionaries[dictionary.dict_id()] = dictionary

def decompress(source):
    frame = zstd.get_frame_parameters(source)
    dictionary = dictionaries.get(frame.dict_id)
    assert frame.dict_id == 0 or dictionary is not None
    return zstd.ZstdDecompressor(dict_data=dictionary).decompress(source)

def compress(source, old):
    frame = zstd.get_frame_parameters(old)
    dictionary = dictionaries.get(frame.dict_id)
    result = zstd.ZstdCompressor(level=19, dict_data=dictionary).compress(source)
    assert zstd.get_frame_parameters(result).dict_id == frame.dict_id
    assert decompress(result) == source
    return result

archive_name = 'UI/LayoutArchive/Common.Product.110.Nin_NX_NVN.blarc.zs'
original_archive_compressed = (romfs / archive_name).read_bytes()
original_archive = decompress(original_archive_compressed)
original_files = sarc(original_archive)
combined = original_files['timg/__Combined.bntx']

def texture_index(bntx):
    count = struct.unpack_from('<I', bntx, 0x24)[0]
    pointer_table = struct.unpack_from('<Q', bntx, 0x28)[0]
    result = {}
    for index in range(count):
        texture = struct.unpack_from('<Q', bntx, pointer_table + 8 * index)[0]
        name_ptr = struct.unpack_from('<Q', bntx, texture + 0x60)[0]
        length = struct.unpack_from('<H', bntx, name_ptr)[0]
        name = bntx[name_ptr + 2:name_ptr + 2 + length].decode()
        result[name] = texture
    return result

textures = texture_index(combined)
template = Path('work/d11/medallion.bntx').read_bytes()
assert template[:4] == b'BNTX' and template[0xb000:0xb004] == b'_RLT'

def bc4_linearize(payload, width, height, block_height):
    blocks_w, blocks_h = (width + 3) // 4, (height + 3) // 4
    pitch = (blocks_w * 8 + 63) // 64
    linear = bytearray(blocks_w * blocks_h * 8)
    for y in range(blocks_h):
        for x in range(blocks_w * 8):
            offset = (y // (8 * block_height)) * 512 * block_height * pitch + (x // 64) * 512 * block_height + ((y % (8 * block_height)) // 8) * 512 + ((x % 64) // 32) * 256 + ((y % 8) // 2) * 64 + ((x % 32) // 16) * 32 + (y % 2) * 16 + x % 16
            linear[y * blocks_w * 8 + x] = payload[offset]
    return bytes(linear)

def bc4_swizzle(linear, width, height, block_height, image_size):
    blocks_w, blocks_h = (width + 3) // 4, (height + 3) // 4
    pitch = (blocks_w * 8 + 63) // 64
    result = bytearray(image_size)
    for y in range(blocks_h):
        for x in range(blocks_w * 8):
            offset = (y // (8 * block_height)) * 512 * block_height * pitch + (x // 64) * 512 * block_height + ((y % (8 * block_height)) // 8) * 512 + ((x % 64) // 32) * 256 + ((y % 8) // 2) * 64 + ((x % 32) // 16) * 32 + (y % 2) * 16 + x % 16
            result[offset] = linear[y * blocks_w * 8 + x]
    assert bc4_linearize(result, width, height, block_height) == linear
    return bytes(result)

def standalone_icon(source_name, output_name, shift_down_blocks=0):
    source_texture = textures[source_name]
    format_ = struct.unpack_from('<I', combined, source_texture + 0x1c)[0]
    width, height = struct.unpack_from('<II', combined, source_texture + 0x24)
    block_height = 1 << (struct.unpack_from('<I', combined, source_texture + 0x34)[0] & 7)
    image_size = struct.unpack_from('<I', combined, source_texture + 0x50)[0]
    table = struct.unpack_from('<Q', combined, source_texture + 0x70)[0]
    data = struct.unpack_from('<Q', combined, table)[0]
    assert format_ == 0x1d01  # Native BC4 alpha mask; tint stays in the native UI material.
    payload = combined[data:data + image_size]
    if shift_down_blocks:
        original_blocks = bc4_linearize(payload, width, height, block_height)
        row_bytes = ((width + 3) // 4) * 8
        shift_bytes = shift_down_blocks * row_bytes
        # The dropped bottom rows are transparent; every visible native block survives.
        rgba = texture2ddecoder.decode_bc4(original_blocks, width, height)
        alpha = Image.frombytes('RGBA', (width, height), rgba, 'raw', 'BGRA').getchannel('R')
        assert alpha.crop((0, height - 4 * shift_down_blocks, width, height)).getextrema() == (0, 0)
        shifted_blocks = bytes(shift_bytes) + original_blocks[:-shift_bytes]
        payload = bc4_swizzle(shifted_blocks, width, height, block_height, image_size)

    bntx = bytearray(template[:0x1000])
    bntx.extend(payload)
    relocation = (len(bntx) + 0xfff) & ~0xfff
    bntx.extend(bytes(relocation - len(bntx)))
    bntx.extend(template[0xb000:])
    struct.pack_into('<II', bntx, 0x18, relocation, len(bntx))
    struct.pack_into('<Q', bntx, 0xff8, relocation - 0xff0)
    bntx[0x208:0x258] = combined[source_texture + 0x10:source_texture + 0x60]
    assert len(output_name) <= 22
    struct.pack_into('<H', bntx, 0x1b8, len(output_name))
    bntx[0x1ba:0x1d0] = output_name.encode() + bytes(22 - len(output_name))
    struct.pack_into('<I', bntx, relocation + 4, relocation)
    struct.pack_into('<I', bntx, relocation + 0x34, relocation - 0xff0)
    assert struct.unpack_from('<Q', bntx, 0x498)[0] == 0x1000
    assert struct.unpack_from('<I', bntx, 0x18)[0] % 4096 == 0
    assert struct.unpack_from('<I', bntx, 0x1f8 + 0x1c)[0] == format_
    assert bntx[0x1000:0x1000 + image_size] == payload
    path = mod / f'romfs/UI/Tex/Icon/{output_name}.bntx.zs'
    path.write_bytes(zstd.ZstdCompressor(level=19).compress(bntx))
    assert zstd.ZstdDecompressor().decompress(path.read_bytes()) == bntx
    return {'source': source_name, 'output': output_name, 'format': hex(format_), 'texture_size': [width, height], 'shift_down_texture_pixels': 4 * shift_down_blocks, 'native_compressed_blocks_preserved': True}

horse_texture = standalone_icon('HakushaFlat_00^s', 'SageHorse')
memory_texture = standalone_icon('MapIconDragonTears_00^s', 'SageMemory', shift_down_blocks=2)

def sections(data):
    position = struct.unpack_from('<H', data, 6)[0]
    while position < len(data):
        kind = data[position:position + 4]
        size = struct.unpack_from('<I', data, position + 4)[0]
        assert size >= 8 and position + size <= len(data)
        yield position, kind, size
        position += size
    assert position == len(data)

def named_pane(data, kind, name):
    hits = [position for position, magic, _ in sections(data)
            if magic == kind and data[position + 12:position + 36].split(b'\0')[0].decode() == name]
    assert len(hits) == 1, (kind, name, hits)
    return hits[0]

def material(data, name):
    positions = [position for position, kind, _ in sections(data) if kind == b'mat1']
    assert len(positions) == 1
    section = positions[0]
    count = struct.unpack_from('<I', data, section + 8)[0]
    hits = []
    for index in range(count):
        offset = struct.unpack_from('<I', data, section + 12 + 4 * index)[0]
        position = section + offset
        if data[position:position + 28].split(b'\0')[0].decode() == name:
            hits.append(position)
    assert len(hits) == 1
    return hits[0]

def edit_button_layout(original, name, scale, tint=None):
    layout = bytearray(original)
    if name != 'PaShortCutMainItemBtn_00':
        assert layout[0x30:0x48] == b'PaShortCutMainItemBtn_00'
        layout[0x30:0x48] = name.encode()
    picture = named_pane(layout, b'pic1', 'P_App_00')
    assert struct.unpack_from('<2f', layout, picture + 0x44) == (0.8500000238418579,) * 2
    assert struct.unpack_from('<2f', layout, picture + 0x24) == (0.0, 0.0)
    struct.pack_into('<2f', layout, picture + 0x44, scale, scale)
    mat = material(layout, 'P_App_00')
    assert layout[mat + 0x24:mat + 0x2c] == bytes.fromhex('00000000ffffffff')
    if tint:
        rgb = bytes.fromhex(tint)
        if name.endswith('_05'):
            layout[mat + 0x24:mat + 0x28] = rgb + b'\0'
        layout[mat + 0x28:mat + 0x2c] = rgb + b'\xff'
    return bytes(layout)

button = 'blyt/PaShortCutMainItemBtn_00.bflyt'
parent = 'blyt/ShortCutMainItem_00.bflyt'
updates = {
    button: edit_button_layout(original_files[button], 'PaShortCutMainItemBtn_00', 1.00),
}
utility_layouts = {
    1: ('Memory', 1.30, 'FFFCC6'),
    5: ('Horse', 0.92, 'CAB52D'),
    7: ('Sleep', 1.05, None),
}
parent_data = bytearray(original_files[parent])
for slot, (_, scale, tint) in utility_layouts.items():
    variant = f'PaShortCutMainItemBtn_{slot:02d}'
    updates[f'blyt/{variant}.bflyt'] = edit_button_layout(original_files[button], variant, scale, tint)
    circle = named_pane(parent_data, b'prt1', f'Pa_Circle_{slot:02d}')
    size = struct.unpack_from('<I', parent_data, circle + 4)[0]
    name_at = parent_data.find(b'PaShortCutMainItemBtn_00', circle, circle + size)
    assert name_at == circle + 0x1a0
    parent_data[name_at:name_at + 24] = variant.encode()
    if slot == 5:
        original_scale = struct.unpack_from('<2f', parent_data, circle + 0x1dc)
        assert all(abs(s - 0.8) < 1e-6 for s in original_scale)
        struct.pack_into('<2f', parent_data, circle + 0x1dc, scale, scale)
    prefix = 'anim/PaShortCutMainItemBtn_00_'
    animations = sorted(k for k in original_files if k.startswith(prefix) and k.endswith('.bflan'))
    assert len(animations) == 7
    for animation in animations:
        assert b'PaShortCutMainItemBtn_00' not in original_files[animation]
        new_name = animation.replace('PaShortCutMainItemBtn_00', variant)
        updates[new_name] = original_files[animation]
updates[parent] = bytes(parent_data)

# Preserve every vanilla UI file and its original offset. Append only the two
# edited layouts, three icon-specific variants and their matching animations.
def rebuild_sarc(original, replacements):
    assert original[:4] == b'SARC' and original[6:8] == b'\xff\xfe'
    data_offset = struct.unpack_from('<I', original, 12)[0]
    count = struct.unpack_from('<H', original, 26)[0]
    multiplier = struct.unpack_from('<I', original, 28)[0]
    names_offset = 32 + count * 16 + 8
    entries = {}
    for index in range(count):
        hash_, attributes, start, end = struct.unpack_from('<4I', original, 32 + index * 16)
        name_at = names_offset + (attributes & 0xffffff) * 4
        name = original[name_at:original.index(0, name_at)].decode()
        assert name not in entries
        entries[name] = (hash_, start, end)
    payload = bytearray(original[data_offset:])
    for name, value in sorted(replacements.items()):
        payload.extend(bytes((-len(payload)) % 8))
        start = len(payload)
        payload.extend(value)
        hash_ = 0
        for byte in name.encode():
            hash_ = (hash_ * multiplier + byte) & 0xffffffff
        if name in entries:
            assert entries[name][0] == hash_
        entries[name] = (hash_, start, len(payload))
    hashes = [value[0] for value in entries.values()]
    assert len(set(hashes)) == len(hashes)
    strings = bytearray()
    rows = []
    for name, (hash_, start, end) in sorted(entries.items(), key=lambda item: item[1][0]):
        strings.extend(bytes((-len(strings)) % 4))
        name_offset = len(strings) // 4
        strings.extend(name.encode() + b'\0')
        rows.append(struct.pack('<4I', hash_, 0x1000000 | name_offset, start, end))
    header = b'SARC' + struct.pack('<HHIIHH', 20, 0xfeff, data_offset + len(payload), data_offset, 0x100, 0)
    header += b'SFAT' + struct.pack('<HHI', 12, len(rows), multiplier) + b''.join(rows)
    header += b'SFNT' + struct.pack('<HH', 8, 0) + strings
    assert len(header) <= data_offset
    result = header + bytes(data_offset - len(header)) + payload
    parsed = sarc(result)
    assert set(parsed) == set(original_files) | set(replacements)
    for name, value in original_files.items():
        assert parsed[name] == replacements.get(name, value), name
    for name, value in replacements.items():
        assert parsed[name] == value
    return result

new_archive = rebuild_sarc(original_archive, updates)
archive_path = mod / 'romfs' / archive_name
archive_path.parent.mkdir(parents=True, exist_ok=True)
archive_path.write_bytes(compress(new_archive, original_archive_compressed))

# The larger UI archive needs one larger allocation; leave every other RESTBL
# entry exactly as it was in the game dump.
restbl_name = 'System/Resource/ResourceSizeTable.Product.121.rsizetable.zs'
old_restbl_compressed = (romfs / restbl_name).read_bytes()
old_restbl = decompress(old_restbl_compressed)
new_restbl = bytearray(old_restbl)
assert old_restbl[:6] == b'RESTBL'
_, _, crc_count, _ = struct.unpack_from('<4I', old_restbl, 6)
target_hash = zlib.crc32(archive_name[:-3].encode())
matches = [22 + i * 8 for i in range(crc_count)
           if struct.unpack_from('<I', old_restbl, 22 + i * 8)[0] == target_hash]
assert len(matches) == 1
old_allocation = struct.unpack_from('<I', old_restbl, matches[0] + 4)[0]
assert old_allocation >= len(original_archive)
new_allocation = (len(new_archive) + 4096 + 31) & ~31
struct.pack_into('<I', new_restbl, matches[0] + 4, new_allocation)
assert [i for i, (a, b) in enumerate(zip(old_restbl, new_restbl)) if a != b] == [
    i for i in range(matches[0] + 4, matches[0] + 8)
    if old_restbl[i] != new_restbl[i]
]
restbl_path = mod / 'romfs' / restbl_name
restbl_path.parent.mkdir(parents=True, exist_ok=True)
restbl_path.write_bytes(compress(new_restbl, old_restbl_compressed))

assert (mod / 'exefs/subsdk4').read_bytes() == (base_mod / 'exefs/subsdk4').read_bytes()
assert (mod / 'exefs/main.npdm').read_bytes() == (base_mod / 'exefs/main.npdm').read_bytes()
assert (mod / 'romfs/EmoteConfig/emotes.json').read_bytes() == (base_mod / 'romfs/EmoteConfig/emotes.json').read_bytes()
assert (mod / 'romfs/EmoteConfig/wheel.json').read_bytes() == (base_mod / 'romfs/EmoteConfig/wheel.json').read_bytes()
changed = sorted(str(p.relative_to(mod)) for p in mod.rglob('*') if p.is_file()
                 and (not (base_mod / p.relative_to(mod)).exists()
                      or p.read_bytes() != (base_mod / p.relative_to(mod)).read_bytes()))
assert changed == sorted([
    'romfs/UI/Tex/Icon/SageHorse.bntx.zs',
    'romfs/UI/Tex/Icon/SageMemory.bntx.zs',
    'romfs/' + archive_name,
    'romfs/' + restbl_name,
]), changed

output.parent.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as packed:
    for path in sorted(mod.rglob('*')):
        if path.is_file():
            packed.write(path, str(path.relative_to(mod.parent)))
with zipfile.ZipFile(output) as packed:
    assert packed.testzip() is None
    assert all(name.startswith('Sage Selector/') for name in packed.namelist())
    assert len(packed.namelist()) == 8
    for path in mod.rglob('*'):
        if path.is_file():
            assert packed.read('Sage Selector/' + str(path.relative_to(mod))) == path.read_bytes()

report = {
    'zip_sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
    'source': 'D21',
    'changed_game_files': changed,
    'ui_archive_uncompressed_bytes': [len(original_archive), len(new_archive)],
    'ui_archive_changed_entries': sorted(updates),
    'restbl_archive_allocation_bytes': [old_allocation, new_allocation],
    'textures': [horse_texture, memory_texture],
    'pane_scales': {'five_sages': 1.0, 'horse': 0.92, 'memory': 1.30, 'sleep': 1.05},
    'material_colors': {'horse': '#CAB52D', 'memory': '#FFFCC6', 'sleep': 'native texture color', 'sages': 'native texture colors'},
    'centering': {'memory_mask_shift_down_texture_pixels': 8, 'pane_offsets': 'unchanged'},
    'executable_unchanged': True,
}
(work / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
print(output, output.stat().st_size, 'bytes', report['zip_sha256'])
