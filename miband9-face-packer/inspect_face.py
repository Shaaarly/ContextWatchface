#!/usr/bin/env python3
"""Parse Band 9 v2 tables, components and RLE images, with range/ref checks.
SPDX-License-Identifier: MIT
Emits a component/resource list, NOT a lossless .fprj (names are not stored).
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from face_codec import resource_frames
from validate_gb import parse_as_watchface


def inspect(data):
    if len(data) < 168 or data[:4] != bytes.fromhex('5aa53412'):
        raise ValueError('Unsupported v2 header')
    result = parse_as_watchface(data)
    count = data[28]
    if not count or 168 + count*88 > len(data):
        raise ValueError('Invalid face count')
    result.update(bytes=len(data), sha256=hashlib.sha256(data).hexdigest(),
                  version=struct.unpack_from('<I', data, 16)[0], flags=data[30], faces=[])
    ranges = [(0, 168+count*88, 'headers')]
    all_resources = {}
    pending_refs = []

    seen_regions = set()

    def region(start, size, label):
        if start < 168+count*88 or start + size > len(data) or start % 4:
            raise ValueError(f'Out of bounds/unaligned {label}: {start:#x}+{size}')
        # A payload several faces share is claimed by each of their index
        # tables. Registering it once keeps the overlap check meaningful:
        # two faces pointing at the SAME bytes is the sharing working, two
        # records straddling each other is still caught.
        if size and (start, size) not in seen_regions:
            seen_regions.add((start, size))
            ranges.append((start, start+size, label))

    decoded = {}

    def decode_resource(start, size, is_list):
        # Cached by position: a shared payload is reached once per face and
        # decoding it again would re-verify identical bytes N times.
        if (start, size) not in decoded:
            w, h, frames = resource_frames(data[start:start+size], is_list)
            decoded[start, size] = {
                'width': w, 'height': h, 'frames': len(frames),
                'decoded_sha256': [hashlib.sha256(raw).hexdigest()
                                   for raw in frames]}
        return decoded[start, size]

    for fi in range(count):
        face = {'index': fi, 'tables': {}, 'components': [], 'resources': []}
        result['faces'].append(face)
        # Each face descriptor carries its own preview at +4, which is what
        # a style picker has to show for that face. 0xffffffff means none,
        # which is what every face but the first used to get. These are not
        # in any index table, so they must be claimed here or the gap check
        # below reads them as unexplained bytes.
        own, = struct.unpack_from('<I', data, 168+88*fi+4)
        if own != 0xffffffff:
            if not own or own + 12 > len(data):
                raise ValueError(f'face{fi} preview pointer out of range')
            size = 12 + struct.unpack_from('<I', data, own+8)[0]
            region(own, size, f'face{fi}/preview')
            face['preview'] = dict(offset=own, size=size,
                                   **decode_resource(own, size, False))
        entries = {}
        for kind in range(10):
            n, table = struct.unpack_from('<II', data, 168+88*fi+8+8*kind)
            if kind not in (0, 2, 3, 4, 7, 9) and n:
                raise ValueError(f'Type {kind} not supported by this inspector')
            region(table, 16*n, f'face{fi}/table{kind}')
            face['tables'][str(kind)] = {'offset': table, 'count': n}
            entries[kind] = []
            for j in range(n):
                ident, reserved, pos, size = struct.unpack_from('<IIII', data, table+16*j)
                if reserved or ident >> 24 != kind:
                    raise ValueError('Invalid resource ID/reserved word')
                region(pos, size, f'face{fi}/type{kind}/id{ident:#x}')
                entries[kind].append((ident, pos, size))
                if kind:
                    # The same ID in two faces' tables is legitimate only
                    # when it names the very same bytes - that is a shared
                    # payload. Pointing one ID at two different payloads is
                    # still a corrupt file.
                    if all_resources.setdefault(ident, (kind, pos, size))                             != (kind, pos, size):
                        raise ValueError(f'Duplicate resource ID {ident:#x}')
                if kind in (2, 3):
                    meta = decode_resource(pos, size, kind == 3)
                    face['resources'].append(dict(id=f'{ident:08x}', offset=pos,
                                                  size=size, **meta))
        # kind4 native animations: 12 B, atlas ID + ms delay + frame count
        animations = {}
        atlas_frames = {r['id']: r['frames'] for r in face['resources']}
        for ident, pos, size in entries[4]:
            if size != 12:
                raise ValueError('Animation record size must be 12')
            # NOT `count`: that name belongs to the face count this
            # function closes over in region(), and rebinding it here made
            # every face after the first fail its own bounds check - a bug
            # that could only ever show up in a file with more than one
            # face AND an animation in it.
            atlas, pad1, delay, frames, pad2 = struct.unpack_from('<IHHHH',
                                                                  data, pos)
            if pad1 or pad2:
                raise ValueError('Nonzero animation reserved words')
            if not 0 < frames <= 255 or not 0 < delay <= 65535:
                raise ValueError('Animation delay/count out of range')
            held = atlas_frames.get(f'{atlas:08x}')
            if held is not None and held != frames:
                raise ValueError(f'Animation claims {frames} frames but its '
                                 f'atlas holds {held}')
            pending_refs.append((atlas, 3))
            animations[ident] = {'kind': 'animation',
                                 'animation_id': f'{ident:08x}',
                                 'image_id': f'{atlas:08x}',
                                 'delay_ms': delay, 'frames': frames,
                                 'offset': pos, 'size': size}
        # kind9 shortcut actions: 56 B, marker + action code + tap image.
        # Decoded back out so a build carrying one is still fully verified
        # structurally; what the action code MEANS to the firmware is not
        # something this file can check.
        actions = {}
        for ident, pos, size in entries[9]:
            if size != 56:
                raise ValueError('Action record size must be 56')
            tag = data[pos:pos+2]
            code = data[pos+40:pos+44]
            image, = struct.unpack_from('<I', data, pos+48)
            w, h = struct.unpack_from('<HH', data, pos+52)
            if any(data[pos+2:pos+40] + data[pos+44:pos+48]):
                raise ValueError('Nonzero action reserved words')
            if not w or not h:
                raise ValueError('Action tap area must be non-empty')
            pending_refs.append((image, 2))
            actions[ident] = {'kind': 'shortcut', 'action_id': f'{ident:08x}',
                              'action_code': code.hex().upper(),
                              'action_tag': tag.hex().upper(),
                              'image_id': f'{image:08x}', 'width': w,
                              'height': h, 'offset': pos, 'size': size,
                              'firmware_behaviour': 'NOT_VERIFIED'}
        widgets = {}
        for ident, pos, size in entries[7]:
            if size < 16:
                raise ValueError('Widget record too short')
            source = data[pos:pos+2].hex().upper()
            family = data[pos+3] & 0xf0
            image, = struct.unpack_from('<I', data, pos+8)
            pending_refs.append((image, 2 if family == 0x30 else 3))
            meta = {'widget_id': f'{ident:08x}', 'source': source,
                    'firmware_source': f'0x{int.from_bytes(data[pos:pos+2], "little"):04X}',
                    'image_id': f'{image:08x}', 'offset': pos, 'size': size}
            if family == 0x10:
                if size != 20:
                    raise ValueError('Number record size must be 20')
                meta.update(kind='number', digits=data[pos+2], alignment_bits=data[pos+3]&3,
                            blanking=not bool(data[pos+3]&4), spacing=data[pos+13])
            elif family == 0x20:
                if (size-16) % 4:
                    raise ValueError('Invalid custom-value map size')
                meta.update(kind='image_list', values=list(struct.unpack_from('<'+'i'*((size-16)//4), data, pos+16)))
            elif family == 0x30:
                if size != 32:
                    raise ValueError('Hand record size must be 32')
                meta.update(kind='analog_hand', period=data[pos+17],
                            pivot=list(struct.unpack_from('<HH', data, pos+20)),
                            maximum=struct.unpack_from('<H', data, pos+26)[0])
            else:
                raise ValueError(f'Unsupported widget family {family:#x}')
            widgets[ident] = meta
        for ident, pos, size in entries[0]:
            if size != 16:
                raise ValueError('Element record size must be 16')
            target, x, y, reserved1, reserved2 = struct.unpack_from('<IhhII', data, pos)
            if reserved1 or reserved2:
                raise ValueError('Nonzero element reserved words')
            if target in widgets:
                meta = dict(widgets[target])
            elif target in animations:
                meta = dict(animations[target])
            elif target in actions:
                meta = dict(actions[target])
            elif target >> 24 == 2:
                meta = dict(kind='image', image_id=f'{target:08x}')
            else:
                raise ValueError('Element refers to missing widget')
            pending_refs.append((target, target >> 24))
            meta.update(element_id=ident, element_offset=pos, x=x, y=y)
            face['components'].append(meta)
    for ident, kind in pending_refs:
        held = all_resources.get(ident)
        if held is None or held[0] != kind:
            raise ValueError(f'Dangling/wrong-type reference {ident:#x}')
    preview, = struct.unpack_from('<I', data, 32)
    if not preview or preview+12 > len(data):
        raise ValueError('Missing preview resource')
    preview_size = 12 + struct.unpack_from('<I', data, preview+8)[0]
    region(preview, preview_size, 'preview')
    result['preview_resource'] = dict(offset=preview, size=preview_size,
                                      **decode_resource(preview, preview_size, False))
    end = 0
    for start, stop, label in sorted(ranges):
        if start < end:
            raise ValueError(f'Overlapping records: {label}')
        if any(data[end:start]):
            raise ValueError(f'Nonzero unexplained gap before {label}')
        end = stop
    if len(data)-end > 3 or any(data[end:]):
        raise ValueError('Unexplained trailing bytes')
    result['structural_validation'] = 'PASS (ranges, references, sizes, all RLE frames)'
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('face', type=Path)
    ap.add_argument('--output', type=Path)
    args = ap.parse_args()
    try:
        text = json.dumps(inspect(args.face.read_bytes()), ensure_ascii=False, indent=2) + '\n'
        if args.output:
            args.output.write_text(text, encoding='utf-8')
            print(f'OK parsed {args.face} -> {args.output}')
        else:
            print(text, end='')
    except (ValueError, OSError, struct.error) as exc:
        ap.exit(2, f'FAIL: {exc}\n')


if __name__ == '__main__':
    main()
