# miband9-face-packer

A pure-Python compiler that turns a [Mi Create](https://github.com/ooflet/Mi-Create) project (`.fprj` + `images/`) for the **Xiaomi Smart Band 9** (`DeviceType="366"`, 192×490) into an installable v2 `.face` watchface — **on macOS or Linux, with no Windows, Wine, Mono or .NET**.

Monorepo context (agents / contributors): [`../docs/CONTEXT.md`](../docs/CONTEXT.md), [`../AGENTS.md`](../AGENTS.md) (Cursor), [`../CLAUDE.md`](../CLAUDE.md) (Claude Code), [`../docs/STATUS.md`](../docs/STATUS.md), [`../docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md), [`../docs/AUTHORING.md`](../docs/AUTHORING.md).

Mi Create currently relies on the closed-source Windows `compile.exe` and shows *"macOS compiler support will be added soon."* on macOS. This project is an independent reimplementation of the Band 9 packing path.

## Status

- **Byte-exact** with the original compiler on a public Band 9 project: rebuilding [Vadim170/miband9-minimal-analog](https://github.com/Vadim170/miband9-minimal-analog) (commit `1249c46`, 2 faces + AOD, 146 image frames) produces a file identical to the shipped `AnalogFull.face` (1,094,548 bytes, SHA-256 `d531249c…03b3`).
- **Tested on a real Band 9** (CN model) installed through [Gadgetbridge](https://gadgetbridge.org/) 0.95.1: digital numbers bound to time, weather temperature (`2031`) and AQI (`5031`), plus a 101-frame image-list progress bar, all render and update.
- Only one device is supported. Other v2 devices (Band 8, Redmi Watch…) are **not** tested.

## Requirements

Python ≥ 3.10 and Pillow (`pip install Pillow`).

## Usage

```bash
# compile a project directory (containing *.fprj, images/, optional AOD/) or a .fprj file
python3 pack_face.py <project-dir-or.fprj> <out.face> [--id 123456789]

# offline check that mirrors Gadgetbridge's XiaomiFWHelper.parseAsWatchface()
python3 validate_gb.py <file.face>

# decode a .face back into a JSON component list (also validates every RLE frame)
python3 inspect_face.py <file.face> [--output components.json]

# generate a tiny probe project (time + 2031 + 5031) into samples/minimal/
python3 make_minimal.py
```

`--id` is the 9-digit ASCII ID written at offset `0x28` (Gadgetbridge uses it as the watchface ID; use a different ID per face). Data sources are the hex strings in `Value_Src` / `Index_Src`, exactly as Mi Create writes them.

## Supported features

Supported: Shape 30 static image, 31 indexed image list, 32 digital number, 27 analog clock hands, `AOD/` sub-project, multiple `.fprj` in one directory, PNG input (RGB565 + alpha, Band 9 RLE).

`--face-previews` writes every face's own preview image (its own Screen Bitmap) instead of only the first, which the original compiler left at `0xffffffff` — no image — for every face after face 0. It packs, but **firmware ignores it**, so it gives no per-style card in the picker: leave it off (see [`../docs/STATUS.md`](../docs/STATUS.md)). `--main-preview` sets the file's own preview (`+0x20`) independently; it is meant for a phone's watch face list, which is **not verified on hardware**.

`--share-resources` writes one copy of any image or atlas that several faces use, each face's index table pointing at it — for style sets, where the faces are the same panel with one detail changed and a full copy per style is otherwise the whole file again. Table counts are unaffected; only where an entry points changes. Off by default, so output is unchanged without it. Whether firmware offers a picker for a multi-face file is **not verified**.

**Packed from the static format description, not from a sample:** `anim_[count@delay]` kind4 native animations and `btn_[target]` kind9 tap shortcuts. Both have since been **confirmed working on a real Band 9** (CN model, via Gadgetbridge). A `btn_` widget must be Shape 30 and must carry `Action_Code` (8 hex digits); this repository deliberately ships **no table of action constants**, so the caller supplies the code. The optional `Action_Tag` fills the 2-byte marker at +0, which has no observed value and defaults to zero. Build a shortcut-free file alongside any build that uses one.

Rejected with an explicit error (never silently dropped): arc/line progress (Shape 29/42), apps (`app_`), bare `btn_`/`anim_` names without the bracketed form, other unknown shapes, non-366 devices. Contributions welcome.

## Tests

```bash
python3 -m unittest discover -s . -v
# byte-exact reference test (skipped unless the sample is present):
git clone https://github.com/Vadim170/miband9-minimal-analog
MINIMAL_ANALOG_DIR=./miband9-minimal-analog python3 -m unittest discover -s . -v
```

## How it was made (provenance)

The file format was recovered by **statically decompiling** `compile.exe` 4.22 (m0tral's Mi Watch compiler, bundled with Mi Create) with ILSpy, cross-checked against [RedKage/Xiaomi_Band_Tools](https://github.com/RedKage/Xiaomi_Band_Tools) and the Gadgetbridge parser. The decompiled code is **not** included here; this repository is a fresh Python implementation written from the recovered format description in [`docs/FORMAT.zh-CN.md`](docs/FORMAT.zh-CN.md) (Chinese). The original binary was never executed. Development was AI-assisted.

All credit for the format and the original tooling goes to **m0tral** (EasyFace / Mi Watch compiler) and **ooflet** (Mi Create). If the original author objects to this reimplementation, please open an issue.

## Disclaimer

Installing third-party watchfaces is at your own risk. Gadgetbridge warns that a watchface for the wrong device can brick it. This project is not affiliated with Xiaomi.

## License

MIT
