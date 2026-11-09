# Autoría de watch faces

Aplica al trabajar en `.fprj` / `ejemplo-verificado/`. Canónico: `docs/AUTHORING.md`.

## Dispositivo y sources

- `FaceProject DeviceType="366"` únicamente.
- Sources Band 9: `1812` día, `2012` semana (0=domingo), `0841` batería, agujas `0811/1011/1811`.
- No usar códigos genéricos `xiaomi_color` (11/12/20…) — en hardware leen 0.

## Widgets

- Orden XML = z-order (último encima).
- Shape 31: entradas `(N):file.png`. Shape 32: `0.png|…|9.png`.
- `btn_[destino]`: Shape 30, bitmap transparente, `Action_Code` 8 hex; último en la lista.
- `anim_[n@ms]`: `BitmapList` con exactamente `n` frames.
- Jump codes: tabla en `docs/AUTHORING.md` (no en runtime).

## Ejemplo verificado

- `AnalogFull.face` es golden; no editarlo a mano — recompilar con el packer.
- Path principal de build: `miband9-face-packer/pack_face.py`, no Wine/`compile.exe`.
- `tools/build_sim.py` está desfasado; no regenerar `simulator.html` con él.

## Sync

Espejo de `.cursor/rules/authoring.mdc`. Al cambiar política, actualizar ambos.
