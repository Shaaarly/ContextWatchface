# Arquitectura

Estado actual vs dirección. Detalle de soporte: [`STATUS.md`](STATUS.md).

## Mapa del monorepo

```text
ContextWatchface/
├── README.md                 # entrada GitHub (uso humano + context)
├── AGENTS.md / CLAUDE.md     # boot Cursor vs Claude Code (mismas obligaciones)
├── LEEME.md                  # guía rápida de usuario (ES)
├── .cursor/rules/ · .claude/rules/  # rules espejo
├── docs/                     # CONTEXT, STATUS, QUICKSTART, AUTHORING, ARCHITECTURE
├── miband9-face-packer/      # compilador .fprj → .face
│   ├── pack_face.py          # parse + compile + CLI (hoy monolítico)
│   ├── face_codec.py         # PNG → RGB565+A → RLE Band 9
│   ├── inspect_face.py       # .face → JSON + verificación de frames
│   ├── validate_gb.py        # gate offline estilo Gadgetbridge
│   ├── make_minimal.py       # proyecto sonda
│   ├── test_compiler.py
│   └── docs/FORMAT.zh-CN.md  # especificación binaria (histórica; cruzar con STATUS)
└── ejemplo-verificado/       # golden project + AnalogFull.face
    ├── AnalogFull.fprj
    ├── AOD/
    ├── images/
    ├── tools/                # generadores de assets (Pillow)
    └── simulator.html
```

## Flujo de datos (actual)

```text
.fprj + images/ (+ AOD/)
        │
        ▼
  pack_face.parse_project / find_projects
        │  IR: Face + Item
        ▼
  pack_face.compile_project
        │  usa face_codec.image_resource
        ▼
     bytes .face
        │
   ┌────┴────┐
   ▼         ▼
validate_gb  inspect_face
 (GB gate)   (tablas + RLE)
```

Instalación en dispositivo queda **fuera** del toolchain (Gadgetbridge / apps).

## Fronteras de responsabilidad

| Pieza | Debe | No debe |
|---|---|---|
| `pack_face` (hoy) | descubrir proyectos, parsear XML, empaquetar | instalar en reloj |
| `face_codec` | píxeles ↔ recurso RLE | conocer widgets / sources |
| `inspect_face` | leer/verificar `.face` | regenerar `.fprj` lossless |
| `validate_gb` | imitar parse GB + size gate Band 9 | firmar ni flashear |
| `ejemplo-verificado/tools` | dibujar PNG + escribir `.fprj` | definir el formato binario |
| Docs `STATUS` | verdades verificadas | tutorial largo |

## Capas objetivo (refactor futuro)

Sin cambiar el contrato byte-exact ni la CLI pública (shims OK):

```text
CLI → Application (compile/find)
    → Domain (Face IR, widget parsers, DeviceProfile)
    → Binary packer (header, tables, payloads)
    → Codec (PNG / RLE)
```

Reglas de diseño al partir código:

1. **IR intermedio** (`Face` / `Item`) como frontera estable parse ↔ pack.
2. **Registry de widgets** por Shape / nombre especial (`anim_`, `btn_`).
3. **`DeviceProfile`** concentra `DeviceType`, tamaño, codec y gates — Band 8/10 solo vía perfil nuevo.
4. **Fail closed** se mantiene: desconocido = `ValueError`.
5. Jump codes de botones **no** entran al runtime; viven en docs de autoría.

## Extensiones locales (parches sobre upstream)

Respecto a [brigealong/miband9-face-packer](https://github.com/brigealong/miband9-face-packer):

| Parche | Capa |
|---|---|
| `anim_[n@ms]` kind4 | parse nombre + payload animación |
| `btn_[…]` kind9 | parse Shape 30 + `Action_Code` + payload action |
| `--share-resources` | allocate de imágenes/atlas compartidos |
| `--face-previews` | descriptor preview; firmware lo ignora |

## Tests como anclas

| Test | Protege |
|---|---|
| Codec roundtrip / RLE | `face_codec` |
| Compile minimal + GB gate | header + números básicos |
| `btn_` / `anim_` en suite | parches locales |
| Byte-exact `MINIMAL_ANALOG_DIR` | paridad con `compile.exe` 4.22 |

Al tocar packing o codec: ejecutar la suite con el ejemplo verificado presente.
