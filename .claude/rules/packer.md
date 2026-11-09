# Packer

Aplica al trabajar en `miband9-face-packer/**/*.py`.

## Módulos actuales

- `pack_face.py` — discovery, parse `.fprj`, packing, CLI
- `face_codec.py` — PNG → RGB565+A → RLE (sin lógica de widgets)
- `inspect_face.py` / `validate_gb.py` — lectura / gate GB offline

## Al editar

- Mantener `DeviceType == "366"` como rechazo explícito.
- Parches locales: `anim_[n@ms]` (kind4), `btn_[name]` + `Action_Code` (kind9).
- `btn_` solo Shape 30; PNG de hit-area transparente; caller aporta el código hex.
- `Alpha` solo 255, `Visible_Src` solo 0.
- Tras cambios de packing/codec: unittest; con ejemplo presente, byte-exact.

```bash
cd miband9-face-packer
MINIMAL_ANALOG_DIR=../ejemplo-verificado python -m unittest discover -s .
```

## Refactor

Separar capas según `docs/ARCHITECTURE.md` sin romper nombres CLI (`pack_face.py` como shim OK). Codec no debe importar widgets.

## Sync

Espejo de `.cursor/rules/packer.mdc`. Al cambiar política, actualizar ambos.
