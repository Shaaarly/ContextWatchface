# Mi Band 9 — "Analog Full" watchface

> **Monorepo banner (2026-11-09):** In this WatchFace kit, compile with
> `../miband9-face-packer/pack_face.py` — **not** Wine/`compile.exe` as the primary path.
> Weekday `Index_Src=2012` is **0=Sunday … 6=Saturday** (confirmed in `../docs/STATUS.md`).
> Support matrix and agent context: `../docs/STATUS.md`, `../docs/AUTHORING.md`,
> `../docs/CONTEXT.md`. Sections below that still describe Wine-only builds or an
> unverified weekday base are **historical** relative to this monorepo.

> This is the detailed documentation. The project was built by Claude (Anthropic's Claude Code); the human owner did not read the code.

A custom watchface for the **Xiaomi Smart Band 9**: a round analog dial with all 12
numerals, a live date at the top and battery percentage at the bottom. Black (AMOLED)
background, monochrome high-contrast design (the battery readout changes color by level).

The project is hand-built in the **`.fprj`** format (the format used by the
[Mi Create](https://github.com/ooflet/Mi-Create) / EasyFace editor). In this monorepo it
is compiled with the local Python packer into a `.face` binary.

---

## 1. Device parameters

| Parameter | Value |
|---|---|
| Model | Xiaomi Smart Band 9 |
| Display | 192 × 490 px, 1.62″ AMOLED, portrait |
| Corner rounding | 100 px (corner radius) |
| `DeviceType` in `.fprj` | **366** |
| Device identifier | `xiaomi_band_9` |

Source: `Mi-Create/src/data/devices.json`.

---

## 2. Project structure

```
AnalogFull/
├── AnalogFull.fprj        # XML project (6 widgets)
├── README.md              # short English overview
├── DETAILS.md             # full documentation (this file)
├── simulator.html         # live preview simulator (opens in a browser)
├── images/                # all raster assets (filenames ↔ references in .fprj)
│   ├── background.png      # dial + ticks + clock numerals (static; NO icons and NO "%")
│   ├── clock_bg.png        # transparent background of the analog widget (so the dial is not duplicated)
│   ├── hand_hour.png       # hour hand   (full-size 192×490, pivot at center)
│   ├── hand_minute.png     # minute hand
│   ├── hand_second.png     # second hand (red)
│   ├── center_cap.png      # axle cap (on top of the hands)
│   ├── preview.png         # watchface thumbnail (Screen/@Bitmap)
│   ├── b_0…b_100.png       # battery frames "NN%": 101 of them, index = battery %,
│   │                       #   with the "%" sign and the color already baked in (≤5 red, ≤15 yellow, otherwise white)
│   ├── dd_0…dd_9.png       # date digits (cell 34×60, dimmed, 2×)
│   └── wd_0…wd_6.png       # weekdays Sun,Mon,Tue,Wed,Thu,Fri,Sat (imagelist, 2×)
├── AOD/                   # Always-On Display variant (see the "AOD" section)
│   ├── AOD.fprj            # separate AOD project (dim, no second hand)
│   └── images/             # its own assets: aod_bg, aod_hour, aod_minute, empty, …
└── tools/                 # generators (Python + Pillow), see §6
    ├── render.py           # draws all assets + preview + layout.json
    ├── build_project.py    # builds AnalogFull.fprj from layout.json
    ├── build_aod.py        # builds AOD/ (Always-On Display variant)
    ├── build_sim.py        # builds simulator.html
    └── layout.json         # single source of truth for widget coordinates
```

**Format rule:** image filenames in the `.fprj` are specified relative to the `images/`
folder.

---

## 3. Watchface composition (`.fprj` widgets)

Widget order = draw order (the last one is drawn on top).

| # | Name | Shape | Purpose | Data binding |
|---|---|---|---|---|
| 1 | `bg` | 30 | Static background: dial, ticks, numerals 1–12 (no icons, no "%") | — |
| 2 | `weekday` | 31 | Day of week (image from a list) | `Index_Src=2012` (Week) |
| 3 | `day` | 32 | Day of month | `Value_Src=1812` (Day) |
| 4 | `battery` | 31 | Battery "NN%" — imagelist of 101 colored frames, index = battery % | `Index_Src=0841` (Battery percent) |
| 5 | `analog_clock` | 27 | Hour/minute/second hands | rotation by time |
| 6 | `center_cap` | 30 | Axle cap on top of the hands | — |

> **The battery is an imagelist (Shape 31), not a number (Shape 32).** 101
> pre-rendered frames `b_0.png…b_100.png` are selected by the value of `Index_Src=0841`
> (battery percentage). Every frame already has the "%" sign **and the color** baked in:
> **≤5% red, ≤15% yellow, otherwise white**. In the Mi Create format, numeric widgets have
> no color or threshold attribute (verified), so a colored battery readout is only
> achievable this way — as a pre-colored list of images indexed by the value itself. The
> frame is centered on the dial axis (`X=40, Width=112`). The step counter has been removed
> from the watchface.

---

## 4. `.fprj` format reference

Root:
```xml
<FaceProject DeviceType="366" Id="167210065">
  <Screen Title="Analog Full" Bitmap="preview.png">
    <Widget .../>
  </Screen>
</FaceProject>
```

### Widget type codes (`Shape`)
| Shape | Type | Purpose |
|---|---|---|
| 27 | `widget_analog` | Analog clock (background + 3 hands) |
| 30 | `widget` | Static image (`@Bitmap`) |
| 31 | `widget_imagelist` | List of images, index from a source |
| 32 | `widget_num` | Numeric value made of digit images |
| 34 | `widget_container` | Container group |
| 42 | `widget_arc` | Arc/progress (29 — deprecated) |

### Key attributes

**Common:** `Shape`, `Name`, `X`, `Y`, `Width`, `Height`, `Alpha` (0–255),
`Visible_Src` (0 = always visible).

**Analog clock (Shape 27):**
`Background_ImageName`, `BgImage_rotate_xc/yc`,
`HourHand_ImageName` + `HourImage_rotate_xc/yc`,
`MinuteHand_Image` + `MinuteImage_rotate_xc/yc`,
`SecondHand_Image` + `SecondImage_rotate_xc/yc`,
`HourHandCorrection_En` / `MinuteHandCorrection_En` (smooth movement, 0/1).
`*_rotate_xc/yc` — the rotation point **inside the hand image** (in px).

> **Hand correction.** `*Correction_En=1` makes a hand move smoothly relative to the
> smaller unit: the hour hand creeps along with the minutes (`(h + m/60)·30°`), the minute
> hand with the seconds (`(m + s/60)·6°`). With `=0`, the hand jumps in steps of its own
> unit. For natural analog motion **both must be `1`** — that is how this project is set up
> (previously the hour hand was `0`, which made it jump by the hour without taking minutes
> into account).

> In this project the hands are **full-size 192×490** with the pivot exactly at the center
> of the dial `(96, 245)`, so `rotate_xc=96, rotate_yc=245`. This trick is independent of
> how exactly the engine interprets the anchor — the pivot, the widget center and the dial
> center all coincide.

**Image (Shape 30):** `Bitmap`.

**Imagelist (Shape 31):** `BitmapList`, `Index_Src`, `DefaultIndex`.

**Num (Shape 32):** `BitmapList`, `Value_Src`, `Digits`, `Alignment`, `Blanking`, `Spacing`.

### `BitmapList` format
A list of image names separated by `|`:
- **Num (Shape 32):** strictly the order of digits `0.png|1.png|…|9.png` (index = digit value).
- **Imagelist (Shape 31):** every entry **must** carry an explicit index using the
  `(N):file.png` syntax, e.g. `(0):wd_0.png|(1):wd_1.png|…`. The `Index_Src` value selects
  the file with the matching `N`. Without the `(N):` prefixes, the Mi Create compiler crashes
  on Shape 31.

### `Alignment`
`0 = Left`, `1 = Center`, `2 = Right`. `Blanking=1` blanks leading zeros.

---

## 5. Data sources (`Value_Src` / `Index_Src`)

> 🛑 **KEY POINT: Mi Band 9 uses the `xiaomi_band_9` source table, NOT the generic
> `xiaomi_color` codes (11/12/20/23).** Generic codes read as **0** on Band 9 hardware —
> that was exactly the "date/weekday/battery always 0/Sun" bug. Use only the Band 9 codes
> below.

**Band 9 codes (`xiaomi_band_9` in `Mi-Create/src/data/sources.json`) — used in the project:**

| ID | Source | Usage |
|---|---|---|
| **`1812`** | Day (day of month) | `day` widget (`Value_Src`) |
| **`2012`** | Week (0=Sun … 6=Sat) | `weekday` widget (`Index_Src`) |
| **`0841`** | Battery percent | `battery` widget (`Index_Src`; leading zero — stored as a string) |
| `0821` | Current step count | (steps; for reference, not used in the watchface) |

**Generic `xiaomi_color` table (for other devices / other watchfaces; does NOT work on
Band 9 — returns 0):** Day=`11`, Week=`12`, Battery percent=`20`,
Current step count=`23`, Heart rate=`21`, Step target=`24`, Goal achieve of step (%)=`31`.

> ⚠️ Previously the project mistakenly used exactly these generic codes (`11/12/20/23`),
> hence the zeros on the device. When opening it in the editor, double-check that the
> dropdowns have the sources selected from the **Mi Band 9** table.

> ⚠️ **The weekday base has not been verified on the device.** The simulator and the
> `wd_0…wd_6` set assume `0=Sun … 6=Sat` (like `Date.getDay()`). If the Band 9 firmware
> numbers the week from Monday (`0=Mon`), all days will shift by one — this needs to be
> confirmed on hardware. In the simulator it is fixed with a single line (`SOURCES[2012]`);
> in the project, by reordering the `wd_*` images in the `BitmapList`.

---

## 6. How to rebuild the assets

Requires Python 3 + Pillow.

```bash
python3 -m venv venv && ./venv/bin/pip install Pillow

# 1) draw all images + preview + layout.json (prints a fit-check)
./venv/bin/python tools/render.py .

# 2) build the .fprj from layout.json
./venv/bin/python tools/build_project.py

# 3) build the simulator
./venv/bin/python tools/build_sim.py
```

> ⚠️ **`build_sim.py` is outdated and will overwrite the current `simulator.html`.** The
> generator still emits the old version (assets in base64, numerals/weekday drawn via
> `fillText`). The current `simulator.html` is a **universal engine** (see §8) and is
> maintained **by hand**. Do not run step 3, or first rewrite `build_sim.py` for the new
> renderer. Steps 1–2 (`render.py`, `build_project.py`) are safe and do not touch
> `simulator.html`.

- `render.py` draws with 4× supersampling (anti-aliasing), then downscales to 192×490, and
  prints a **placement check**: every numeral, the dial and both text rows are within the
  screen.
- `layout.json` is the single source of coordinates: both the `.fprj` and the simulator take
  positions from it, so they always stay consistent.
- Paths to the project folder (`PROJ`) in `build_project.py` / `build_sim.py` are set
  absolutely — fix them when relocating.

### Design constants (in `render.py`)
- Dial center `(96, 245)`, radius `R=96` (full width).
- Clock numerals: the row radius is `R_NUM`; font sizes are `fs` (non-cardinal) / `fb`
  (cardinal 12/3/6/9) in `build_background()`. The concrete values are kept only in code and
  edited by hand (the radius ceiling is the screen edge, 192px, for numerals 3/9).
- Tick marks: the radius is `R_TICK_OUT` (edited by hand; may deliberately extend beyond the
  screen edges).
- The minute hand is white, the second hand is red; both hands are full-size.
- **The date/weekday/battery font is doubled (2×):** weekday 48px, date digits 54px, battery
  "NN%" 46px.
- Date at the top (`DATE_Y=30`, pushed toward the top edge, far from the center), battery at
  the bottom (`STAT_Y=420`, pushed toward the bottom edge). Both date and battery are
  **centered on the dial axis** (`WD_X = CX − (row width)/2`, `BATT_X = CX − 112/2 = 40`).
- Battery color by level: `batt_color()` — ≤5% red, ≤15% yellow, otherwise white; the color
  is "baked" into each `b_*.png` frame.

---

## 7. AOD (Always-On Display)

Band 9 supports AOD (`Settings → Display → Always-on display`). With AOD enabled, battery
life drops from ~21 to ~9 days, so the AOD variant must be **low-power**: fewer lit pixels,
dim colors, **a once-per-minute refresh → no second hand**.

**How it works in the format.** AOD is a nested subproject: an `AOD/` directory with its own
`AOD.fprj` and `AOD/images/`. The Mi Create compiler picks it up automatically
(`exporter.py` looks for an `AOD` folder) and places it in the same `.bin` next to the main
watchface — there is no need to compile/upload it separately.

**What is in our AOD variant** (`tools/build_aod.py`):
- dim palette: hands `#b4b4b9`, ticks `#5f5f64`, numerals `#969699`, date `#6e6e73`;
- a sparse dial: **only hour ticks** + **only the large numerals 12/3/6/9**;
- **only the hour and minute** hands (both with smoothing `*Correction_En=1`); the second
  hand is disabled via a transparent image `empty.png`;
- a dim live date (weekday + day of month), like the main face; battery/steps removed.

**`AOD.fprj` widgets:** `bg` (30) · `weekday` (31, `Index_Src=2012`) ·
`day` (32, `Value_Src=1812`) · `analog_clock` (27, hour+minute, second→`empty.png`) ·
`center_cap` (30). The coordinates match the main watchface (taken from `layout.json`), so
the display↔AOD transition is visually stable.

Rebuild: `./venv/bin/python tools/build_aod.py` (it imports helpers from `render.py`, so run
it after that one). It writes `AOD/` and the `tools/` preview `preview_aod_3x.png`.

---

## 8. Compiling to `.bin` and installation

The Mi Create compiler is `compile.exe` (`Mi-Create/src/compiler/`), **Windows only**:
```
compile.exe -b "AnalogFull.fprj" "<output_dir>" "AnalogFull.face" "1461256429"
```
Options on macOS: open the project in Mi Create on Windows (VM/Parallels) and press Compile,
or run `compile.exe` via Wine.

The finished `.bin`/`.face` is uploaded to the band through the **Mi Fitness** app.

### Build artifacts in the repository

| File | What it is |
|---|---|
| `CR.bin.zip` | The compiled **watchface `.bin`** (signature `5A A5 34 12` — Xiaomi binary format), **not a zip**. The `.zip` extension is misleading — it is already a ready firmware file. |
| `AnalogFull\output\AnalogFull.info` | The XML companion to the `.bin`, generated by the compiler (metadata for uploading). |

> ⚠️ **The name `AnalogFull\output\AnalogFull.info` contains backslashes right in the
> filename.** This is a Windows path (`output\AnalogFull.info`) that, when built via
> Wine/transferred to macOS, became a single literal name instead of a nested `output/`
> folder. Such files exist both in the root and in `AnalogFull/`. On Windows it would be a
> normal path — on macOS/Linux it is garbage. It should be deleted and rebuilt with a correct
> `output_dir`.

> ⚠️ **The `.info` metadata does not match the project.** Inside:
> `DeviceType="1"`, `DeviceVersion="7.1.0"`, `DeciceTypeName="Mi Band 7 Pro"`
> (the typo `Decice` is in the format itself). That is, the current `.bin` was built as a
> **Mi Band 7 Pro**, even though the `.fprj` targets **Band 9 (`DeviceType=366`)**.
> `Type`/`DeviceType` in the `.info` is the compiler's internal numbering, not equal to the
> `DeviceType` from the `.fprj`, but `DeciceTypeName` should name the target model. Before
> uploading to a Band 9, rebuild with the correct device, otherwise the watchface will not
> fit the screen/layout.

---

## 9. Preview simulator

`simulator.html` is a **universal Mi Create watchface engine**, not a preview tailored to
this project. It parses the `.fprj` (`DOMParser`) and draws the widgets by their `Shape`,
reading all attributes directly from the XML — using the real bitmaps from `images/`.

**What the engine renders:**
- `Shape 30` — a static image from `@Bitmap`;
- `Shape 31` — an image from `BitmapList` by the index from `Index_Src` (or `DefaultIndex`),
  honoring `Alignment`;
- `Shape 32` — a multi-digit number: glyphs from `BitmapList`, with proper
  `Digits` / `Blanking` (blanking leading zeros) / `Spacing` / `Alignment` logic;
- `Shape 27` — analog clock: background + 3 hands, rotation around `*_rotate_xc/yc`, with the
  **angles computed from the `*Correction_En` flags in the `.fprj`** (no hardcoded smoothing —
  what is in the project is what you see).

**How it is built (not specific to "Analog Full"):**
- the screen size is taken from the `DEVICE[DeviceType]` table (366 → 192×490), otherwise from
  the size of the background image;
- draw order = order of widgets in the XML (= z-order on the device);
- unknown `Shape`s are silently skipped (the engine is extensible);
- missing assets do not break the render — a warning is shown below the screen;
- data sources come from the `SOURCES` table (the only piece of "platform knowledge"): Band 9
  codes `1812`→number, `2012`→weekday, `841`→battery (from `0841`), plus the generic codes
  `11/12/20/23` are kept for other watchfaces.
- `Shape 31` understands the `(N):file.png` prefixes in `BitmapList`: the `Index_Src` value
  selects the file with the matching `N` (so the battery `0841→84` takes `b_84.png`, and the
  weekday takes `wd_*` by index). The battery frames are already colored, so there is no color
  logic in the simulator — it simply draws the selected frame.

**To view another watchface:** the **"Load .fprj…"** button (images are expected in
`./images/`), or place `simulator.html` next to your own project.

**Project loading:** when opened via a local server, the current `AnalogFull.fprj` is picked
up (`fetch`); on a double-click (`file://`, where `fetch` is forbidden) — the embedded backup
copy of the XML. In both cases images are loaded from `images/` by relative path (for
`<img>`/`drawImage` this works even over `file://`).

**Controls:** a "Real time / Demo" toggle (demo is a deterministic date
`2024-06-11 10:09:36`), a "Battery" input field (0–100; selects the colored frame `b_*.png`).
The "Steps" field is kept for compatibility with other watchfaces, but in this watchface it
has no effect (steps removed).

> Previously the simulator was a self-contained page with assets in base64 and drew the
> numerals/weekday with a system font (`fillText`) — i.e. it looked different on the device.
> Now the render uses the real bitmaps, so the preview matches 1:1.

---

## 10. Sources

- Mi Create — https://github.com/ooflet/Mi-Create · docs https://ooflet.github.io/docs
- EasyFace — https://github.com/m0tral/EasyFace
- The format was reverse-engineered from `src/utils/project.py`, `src/data/devices.json`,
  `src/data/sources.json` in the Mi Create repository.
