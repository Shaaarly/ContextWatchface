#!/usr/bin/env python3
"""Offline Band 9 .fprj -> v2 .face compiler; SPDX-License-Identifier: MIT.

Implements static images, indexed image lists, digital numbers, analog hands,
AOD, multiple faces, kind4 animations (`anim_[n@ms]`) and kind9 shortcuts
(`btn_[name]`). Unknown shapes and unknown name-driven features fail closed.
No shell commands, target execution, network or device access.

Shortcut actions are packed from an action code the CALLER supplies in
Action_Code; this file deliberately holds no table of those constants
(see ../docs/AUTHORING.md). anim_/btn_ packing and Band 9 runtime behaviour
are recorded in ../docs/STATUS.md — prefer STATUS over older FORMAT notes.
"""
import argparse
from dataclasses import dataclass, field
from pathlib import Path
import re
import struct
import sys
import xml.etree.ElementTree as ET
from face_codec import image_resource, load_png


@dataclass
class Item:
    kind: str
    attrs: dict
    paths: tuple = ()
    values: tuple = ()
    source: str = ''
    pivot: tuple = (0, 0)
    period: int = 0
    delay: int = 0          # kind4 animation: milliseconds between frames
    code: bytes = b''       # kind9 action: 4-byte action code
    tag: bytes = b''        # kind9 action: 2-byte action-name marker
    maximum: int = 0
    image_id: int = 0
    target_id: int = 0
    element_pos: int = 0
    widget_pos: int = 0


@dataclass
class Face:
    path: Path
    title: str
    preview: str
    items: list
    tables: dict = field(default_factory=dict)
    lists: dict = field(default_factory=dict)


def integer(attrs, key, default=0):
    return int(attrs.get(key, default))


def data_source(text):
    if not re.fullmatch(r'[0-9A-Fa-f]{1,8}', text):
        raise ValueError(f'Invalid hex data source: {text!r}')
    # The compiler accepts its legacy prefix+low-word notation too.
    value = int(text[-4:], 16) + (int(text[:-4], 16) if len(text) > 4 else 0)
    return (value & 0xffff).to_bytes(2, 'big')


def safe_image(base, name):
    # .fprj stores Windows separators. Do not allow paths outside images/.
    if not name:
        raise ValueError('Missing image filename')
    path = (base / name.replace('\\', '/')).resolve()
    if not path.is_relative_to(base.resolve()):
        raise ValueError(f'Image escapes images directory: {name}')
    if path.suffix.lower() != '.png' or not path.is_file():
        raise ValueError(f'Missing PNG: {path}')
    return path


def parse_project(path, main_root):
    xml_bytes = path.read_bytes()
    if b'<!DOCTYPE' in xml_bytes.upper() or b'<!ENTITY' in xml_bytes.upper():
        raise ValueError('DTD/entities are not supported')
    root = ET.fromstring(xml_bytes)
    if root.tag != 'FaceProject' or root.get('DeviceType') != '366':
        raise ValueError(f'Only Band 9 DeviceType=366 is supported: {path}')
    screens = root.findall('Screen')
    if len(screens) != 1:
        raise ValueError('Exactly one Screen required per .fprj')
    screen = screens[0]
    if any(w.tag != 'Widget' for w in screen):
        raise ValueError('Unsupported Screen child')
    items = []
    for node in screen:
        if len(node):
            raise ValueError('Nested widgets/containers are not implemented')
        a = dict(node.attrib)
        name = a.get('Name', '').lower()
        # kind4 native animation, named anim_[count@delay] per the format
        # notes (docs/FORMAT.zh-CN.md section 10). Every other name-driven
        # feature still fails closed.
        animation = re.fullmatch(r'anim_\[(\d+)@(\d+)\]', name)
        # kind9 shortcut action, named btn_[target] the way Mi Create's own
        # fprj->wfDef exporter names them. The target is a label only: the
        # code that actually reaches the firmware comes from Action_Code,
        # because the constant table behind those labels is not part of this
        # project. Every other name-driven feature still fails closed.
        action = re.fullmatch(r'btn_\[([a-z0-9_]{1,24})\]', name)
        if (not animation and not action
                and (name.startswith(('anim_', 'btn_', 'app_', 'lineprogress_'))
                     or any(s in name for s in ('_ref[', '_color[', '_smooth',
                                                '_nocompress')))):
            raise ValueError(f'Unsupported name-driven feature: {name}')
        if integer(a, 'Alpha', 255) != 255 or integer(a, 'Visible_Src') != 0:
            raise ValueError('Only Alpha=255 and Visible_Src=0 are supported')
        x, y = integer(a, 'X'), integer(a, 'Y')
        if not (-32768 <= x <= 32767 and -32768 <= y <= 32767):
            raise ValueError('Coordinates exceed signed 16-bit range')
        shape = integer(a, 'Shape')
        base = path.parent / 'images'
        if animation:
            count, delay = int(animation[1]), int(animation[2])
            paths = tuple(safe_image(base, entry)
                          for entry in a.get('BitmapList', '').split('|')
                          if entry)
            if not 1 <= len(paths) <= 255:
                raise ValueError('Animations must have 1..255 frames')
            if count != len(paths):
                raise ValueError(f'anim_ declares {count} frames, '
                                 f'BitmapList has {len(paths)}')
            if not 1 <= delay <= 65535:
                raise ValueError('Animation delay must be 1..65535 ms')
            items.append(Item('anim', a, paths, delay=delay))
            continue
        if action:
            if shape != 30:
                raise ValueError(f'btn_[{action[1]}] must be Shape=30; a '
                                 f'shortcut owns exactly one image')
            code = a.get('Action_Code', '')
            if not re.fullmatch(r'[0-9A-Fa-f]{8}', code):
                raise ValueError(f'btn_[{action[1]}] needs Action_Code with '
                                 f'exactly 8 hex digits, got {code!r}')
            # The 2-byte field at +0 is described as a marker matching the
            # action *name*; no observed values for it exist, so it is the
            # caller's to set and defaults to zero rather than to a guess.
            tag = a.get('Action_Tag', '0000')
            if not re.fullmatch(r'[0-9A-Fa-f]{4}', tag):
                raise ValueError(f'btn_[{action[1]}] Action_Tag must be 4 hex '
                                 f'digits, got {tag!r}')
            w, h = integer(a, 'Width'), integer(a, 'Height')
            if not (1 <= w <= 65535 and 1 <= h <= 65535):
                raise ValueError('Shortcut Width/Height must be 1..65535')
            items.append(Item('action', a, (safe_image(base, a.get('Bitmap')),),
                              code=bytes.fromhex(code),
                              tag=bytes.fromhex(tag)))
            continue
        if shape == 30:
            items.append(Item('image', a, (safe_image(base, a.get('Bitmap')),)))
        elif shape in (31, 32):
            entries = a.get('BitmapList', '').split('|')
            values, paths = [], []
            for entry in entries:
                if shape == 31:
                    match = re.fullmatch(r'\((-?\d+)\):(.+)', entry)
                    if not match:
                        raise ValueError('Image lists require (index):filename entries')
                    values.append(int(match[1]))
                    entry = match[2]
                paths.append(safe_image(base, entry))
            if not 1 <= len(paths) <= 255:
                raise ValueError('Lists must have 1..255 frames')
            if shape == 32:
                if not 10 <= len(paths) <= 12:
                    raise ValueError('Numeric list needs digits 0..9, optional minus and dot')
                if not 1 <= integer(a, 'Digits') <= 40:
                    raise ValueError('Digits must be in 1..40')
                if integer(a, 'Alignment') not in (0, 1, 2):
                    raise ValueError('Alignment must be 0, 1 or 2')
                if integer(a, 'Blanking') not in (0, 1) or not 0 <= integer(a, 'Spacing') <= 255:
                    raise ValueError('Invalid Blanking or Spacing')
            src = a.get('Value_Src' if shape == 32 else 'Index_Src', '')
            data_source(src)
            items.append(Item('number' if shape == 32 else 'list', a, tuple(paths), tuple(values), src))
        elif shape == 27:
            for hand, image_attr, source, period, maximum in (
                ('Hour', 'HourHand_ImageName', '0811', 24, 7200),
                ('Minute', 'MinuteHand_Image', '1011', 60, 3600),
                ('Second', 'SecondHand_Image', '1811', 60, 3600),
            ):
                image = a.get(image_attr)
                if not image:
                    continue
                # Compatibility with compile.exe 4.22: AOD second hand uses
                # main images/, unlike hour/minute. No fallback is concealed.
                hand_base = main_root / 'images' if hand == 'Second' else base
                pivot = (integer(a, hand + 'Image_rotate_xc'), integer(a, hand + 'Image_rotate_yc'))
                items.append(Item('hand', a, (safe_image(hand_base, image),), source=source,
                                  pivot=pivot, period=period, maximum=maximum))
        else:
            raise ValueError(f'Unsupported widget Shape={shape}: {name}')
    if not items:
        raise ValueError('Screen must contain at least one supported widget')
    return Face(path, screen.get('Title', ''), screen.get('Bitmap', ''), items)


def find_projects(project):
    if project.is_dir():
        paths = sorted(project.glob('*.fprj'))
        if not paths:
            raise ValueError('No .fprj in project directory')
        main = paths[0]
    else:
        main = project
        paths = sorted(main.parent.glob('*.fprj'))
    faces = [main]
    aod_dir = main.parent / 'AOD'
    has_aod = (aod_dir / 'images').is_dir()
    if has_aod:
        aods = list(aod_dir.glob('*.fprj'))
        if len(aods) != 1:
            raise ValueError('AOD/images exists but not exactly one AOD .fprj')
        faces.extend(aods)
    faces.extend(p for p in paths if p != main)
    if len(faces) > 255:
        raise ValueError('Too many faces')
    return main, faces, has_aod


def compile_project(project, face_id='167210065', share_resources=False,
                    face_previews=False, main_preview=None):
    """Compile a project to a v2 .face.

    share_resources collapses image and atlas payloads that several faces
    use to one copy, each face's index table pointing at it. It exists for
    style sets - several faces that are the same panel with one detail
    changed - where the alternative is a full copy of every pixel per
    style: 610 KB each on the Luffy face, against about a kilobyte of
    tables. It is OFF by default and nothing enables it implicitly, so
    every file this compiler produced before it existed is unchanged,
    byte-exact reference sample included. Resource *identity* here is the
    tuple of source PNG paths, which is what the payload is built from.

    face_previews fills every face descriptor's +4 with that face's own
    Screen Bitmap, and main_preview sets the file's own at +0x20
    independently. Both off by default, and KNOWN NOT TO HELP: the format
    documents +4 as the main face's preview with every other face at
    0xffffffff (docs/FORMAT.zh-CN.md section 4), and a Band 9 given one
    card per face showed none of them in its style picker. Kept because a
    negative result is worth being able to reproduce, not because it does
    anything. A style set wants its legend on +0x20, where it is read.
    """
    if not re.fullmatch(r'[0-9]{9}', face_id):
        raise ValueError('ID must be exactly nine ASCII digits')
    main, projects, has_aod = find_projects(Path(project).resolve())
    faces = [parse_project(p, main.parent) for p in projects]
    title = faces[0].title.encode('utf-8')
    if not title or b'\0' in title or len(title) > 63:
        raise ValueError('Title must occupy 1..63 UTF-8 bytes, without NUL')
    data = bytearray(168 + 88 * len(faces))

    def u32(pos, value):
        struct.pack_into('<I', data, pos, value)

    def u16(pos, value):
        struct.pack_into('<H', data, pos, value & 0xffff)

    def allocate(payload):
        pos = len(data)
        data.extend(payload)
        data.extend(b'\0' * (-len(data) % 4))
        return pos

    def record(table, index, ident, pos, size):
        struct.pack_into('<IIII', data, table + 16*index, ident, 0, pos, size)

    data[:4] = bytes.fromhex('5aa53412')
    u32(16, 2048)
    data[28] = len(faces)
    data[30] = (4 if has_aod else 0) | (2 if len(faces) - int(has_aod) > 1 else 0)
    data[40:49] = face_id.encode('ascii')
    data[104:104+len(title)] = title
    # Reserve ALL face index tables before allocating any payload.
    for fi, face in enumerate(faces):
        h = 168 + fi * 88
        u32(h+4, 0xffffffff)
        face.lists = dict.fromkeys(i.paths for i in face.items
                                   if i.kind in ('number', 'list', 'anim'))
        # A shortcut owns a kind2 image (its tap area) and a kind9 record,
        # and no kind7 widget: it has no data source to bind.
        counts = {0: len(face.items),
                  2: sum(i.kind in ('image', 'hand', 'action')
                         for i in face.items),
                  3: len(face.lists),
                  4: sum(i.kind == 'anim' for i in face.items),
                  7: sum(i.kind not in ('image', 'anim', 'action')
                         for i in face.items),
                  9: sum(i.kind == 'action' for i in face.items)}
        for kind in range(10):
            count = counts.get(kind, 0)
            pos = len(data)
            u32(h+8+8*kind, count)
            u32(h+12+8*kind, pos)
            face.tables[kind] = pos
            data.extend(b'\0' * count * 16)
    next_id = {2: 0, 3: 0, 4: 0, 7: 0, 9: 0}
    shared = {}                 # (kind, paths) -> (ident, pos, size)

    def payload_for(kind, paths, is_list):
        """Allocate a resource payload, or hand back one already written.

        Returns (ident, pos, size). The table entry is still written per
        face by the caller: sharing changes where a face's entry POINTS,
        never how many entries it has, so every count reserved up front
        stays correct.
        """
        key = (kind, paths)
        if share_resources and key in shared:
            return shared[key]
        resource_id = ident(kind)
        payload = image_resource(paths, is_list=is_list)
        pos = allocate(payload)
        entry = (resource_id, pos, len(payload))
        if share_resources:
            shared[key] = entry
        return entry

    def ident(kind):
        index = next_id[kind]
        if index > 255:
            raise ValueError(f'Type {kind} resource count exceeds byte-sized reference indices')
        next_id[kind] += 1
        return kind << 24 | index

    for face in faces:
        for index, item in enumerate(face.items):
            item.element_pos = allocate(bytes(16))
            record(face.tables[0], index, index, item.element_pos, 16)
        index = 0
        for item in face.items:
            if item.kind in ('image', 'anim', 'action'):
                continue
            item.target_id = ident(7)
            size = {'number': 20, 'list': 16 + 4*len(item.values), 'hand': 32}[item.kind]
            item.widget_pos = allocate(bytes(size))
            record(face.tables[7], index, item.target_id, item.widget_pos, size)
            index += 1
        index = 0
        for item in face.items:
            if item.kind not in ('image', 'hand'):
                continue
            item.image_id, pos, size = payload_for(2, item.paths, False)
            record(face.tables[2], index, item.image_id, pos, size)
            index += 1
        # Shortcut tap areas land at the tail of the same kind2 table, and
        # only after every real image, so a project with no shortcuts is
        # byte-identical to what this compiler produced before they existed.
        for item in face.items:
            if item.kind != 'action':
                continue
            item.image_id, pos, size = payload_for(2, item.paths, False)
            record(face.tables[2], index, item.image_id, pos, size)
            index += 1
        index = 0
        for item in face.items:
            if item.kind not in ('number', 'list', 'anim'):
                continue
            # face.lists is the dedup WITHIN a face and sets this face's
            # table count; payload_for is the dedup ACROSS faces and sets
            # where the entry points. Both have to run, in that order.
            if face.lists[item.paths] is None:
                list_id, pos, size = payload_for(3, item.paths, True)
                face.lists[item.paths] = list_id
                record(face.tables[3], index, list_id, pos, size)
                index += 1
            item.image_id = face.lists[item.paths]
        # kind4 animation records. 12 B: u32 atlas ID, u16 0, u16 delay (ms),
        # u16 frame count, u16 0. Must run after the atlas loop above so
        # item.image_id is already resolved. Format per docs/FORMAT.zh-CN.md;
        # the original compiler's packing was recovered by decompilation but
        # never exercised on firmware, so this path is unverified by anyone.
        index = 0
        for item in face.items:
            if item.kind != 'anim':
                continue
            item.target_id = ident(4)
            payload = struct.pack('<IHHHH', item.image_id, 0, item.delay,
                                  len(item.paths), 0)
            pos = allocate(payload)
            record(face.tables[4], index, item.target_id, pos, len(payload))
            index += 1
        # kind9 shortcut records. 56 B: u16 action-name marker at +0, the
        # 4-byte action code at +40, the tap area's kind2 image at +48 and
        # its size at +52/+54; everything else zero. Layout per
        # docs/FORMAT.zh-CN.md section 9, recovered by decompiling the
        # original compiler and NEVER run against firmware - by anyone. It
        # is here because it is the only route to a shortcut on this device
        # and the caller asked for one; treat a build that contains an
        # action as a hardware experiment, and keep an action-free build to
        # fall back to. Must run after the kind2 loop so image_id resolves.
        index = 0
        for item in face.items:
            if item.kind != 'action':
                continue
            item.target_id = ident(9)
            payload = bytearray(56)
            payload[0:2] = item.tag
            payload[40:44] = item.code
            struct.pack_into('<I', payload, 48, item.image_id)
            struct.pack_into('<HH', payload, 52,
                             integer(item.attrs, 'Width'),
                             integer(item.attrs, 'Height'))
            pos = allocate(bytes(payload))
            record(face.tables[9], index, item.target_id, pos, len(payload))
            index += 1
        for item in face.items:
            a = item.attrs
            x, y = integer(a, 'X'), integer(a, 'Y')
            if item.kind == 'number':
                glyph_width = load_png(item.paths[0]).width
                alignment = integer(a, 'Alignment')
                extent = glyph_width * integer(a, 'Digits')
                x += extent // 2 if alignment == 1 else (extent if alignment == 2 else 0)
            elif item.kind == 'hand':
                x += integer(a, 'Width') // 2 - item.pivot[0]
                y += integer(a, 'Height') // 2 - item.pivot[1]
            if not (-32768 <= x <= 32767 and -32768 <= y <= 32767):
                raise ValueError('Adjusted anchor exceeds signed 16-bit coordinates')
            e = item.element_pos
            u32(e, item.image_id if item.kind == 'image' else item.target_id)
            u16(e+4, x)
            u16(e+6, y)
            # An animation element points straight at its kind4 record and a
            # shortcut at its kind9 one; neither has a kind7 widget behind it
            # and neither takes an anchor adjustment.
            if item.kind in ('image', 'anim', 'action'):
                continue
            w = item.widget_pos
            data[w:w+2] = data_source(item.source)
            u32(w+8, item.image_id)
            angle = re.search(r'_angle\[(\d+)\]', a.get('Name', '').lower())
            if angle:
                value = int(angle[1])
                u16(w+14, value if 0 < value < 3600 else 0)
            if item.kind == 'number':
                data[w+2] = integer(a, 'Digits')
                align_bits = {0: 1, 1: 2, 2: 0}[integer(a, 'Alignment')]
                data[w+3] = 0x10 | (4 if integer(a, 'Blanking') == 0 else 0) | align_bits
                data[w+13] = integer(a, 'Spacing')
            elif item.kind == 'list':
                data[w+3] = 0x20
                # 4.22 emits a custom-value map even for sequential indices.
                u32(w+12, 512)
                for j, value in enumerate(item.values):
                    u32(w+16+4*j, value & 0xffffffff)
            else:
                data[w+3] = 0x30
                u16(w+6, 1000)
                data[w+17] = item.period
                u16(w+20, item.pivot[0])
                u16(w+22, item.pivot[1])
                u16(w+26, item.maximum)
    # Previews. Two different slots, and they are not the same picture:
    # +0x20 is the file's own, which is what a phone shows in its list of
    # watch faces, while each face descriptor's +4 is that face's. The
    # original compiler only ever filled the first face's, leaving every
    # other at 0xffffffff - no image - which is exactly what a style set
    # cannot afford: a picker whose entries have no thumbnails.
    written = {}

    def preview_resource(name):
        path = safe_image(main.parent / 'images', name)
        if load_png(path).size not in ((192, 490), (122, 310)):
            raise ValueError(f'Band 9 preview must be 192x490 or 122x310: '
                             f'{name}')
        if path not in written:
            written[path] = allocate(image_resource((path,)))
        return written[path]

    if face_previews:
        for fi, face in enumerate(faces):
            u32(168 + 88*fi + 4, preview_resource(face.preview))
    main_pos = preview_resource(main_preview or faces[0].preview)
    u32(32, main_pos)
    if not face_previews:
        # unchanged from before this option existed, to the byte
        u32(168+4, main_pos)
    return bytes(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project', type=Path, help='Directory or main .fprj (recommended for multi-face projects)')
    parser.add_argument('output', type=Path)
    parser.add_argument('--id', default='167210065', help='Nine numeric digits; default matches compile.exe')
    parser.add_argument('--share-resources', action='store_true',
                        help='write one copy of any image or atlas that '
                             'several faces use, each face pointing at it. '
                             'For style sets; changes the bytes, so it is '
                             'off unless asked for.')
    parser.add_argument('--face-previews', action='store_true',
                        help="fill every face descriptor's +4 with that "
                             "face's Screen Bitmap. The format has that "
                             "field as 0xffffffff for every face but the "
                             "main one, and a Band 9 ignored it: tried, "
                             "inert, kept only so it can be re-tried")
    parser.add_argument('--main-preview', default=None, metavar='NAME.png',
                        help="the file's own preview, shown in a phone's "
                             "watch face list; defaults to the first face's")
    args = parser.parse_args()
    try:
        result = compile_project(args.project, args.id, args.share_resources,
                                 args.face_previews, args.main_preview)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(result)
        print(f'OK {args.output}: {len(result)} bytes, id={args.id}, faces={result[28]}')
    except (ValueError, OSError, ET.ParseError) as exc:
        parser.exit(2, f'ERROR: {exc}\n')


if __name__ == '__main__':
    main()
