# Estado del proyecto

Última revisión: 2026-11-09.

Fuente de verdad de **qué funciona** frente a docs satélite que puedan diverger
(`LEEME.md`, READMEs, comentarios en código, `FORMAT.zh-CN.md`).

## Hardware / instalación

| Afirmación | Estado |
|---|---|
| Xiaomi Smart Band 9, `DeviceType="366"`, 192×490 | **Soportado** |
| Instalación vía Gadgetbridge (parser offline `validate_gb.py`) | **Soportado** (instalación real: Band 9 CN + GB 0.95.1) |
| Band 8 / Band 10 / otros v2 | **No soportado** — el packer rechaza `DeviceType != 366` |
| Notify / Mi Fitness como instaladores | **Fuera de alcance del toolchain**; el ejemplo menciona Mi Fitness |
| Esfera de otro modelo | **Riesgo de brick** — no instalar |

## Contrato de no-regresión

| Artefacto | Valor |
|---|---|
| Proyecto | `ejemplo-verificado/` ([Vadim170/miband9-minimal-analog](https://github.com/Vadim170/miband9-minimal-analog) @ `1249c46`) |
| Salida esperada | `ejemplo-verificado/AnalogFull.face` |
| Tamaño | 1 094 548 bytes |
| SHA-256 | `d531249c5c2f2335ce00b464cf75007d82dd0dc750bd26116bbe5fc3187003b3` |
| ID de prueba | `167210065` |

Cualquier cambio en el packer debe seguir generando ese fichero **byte a byte**
cuando se compila el ejemplo con ese ID.

```bash
cd miband9-face-packer
python pack_face.py ../ejemplo-verificado salida.face --id 167210065
# sha256 de salida.face == d531249c…03b3
MINIMAL_ANALOG_DIR=../ejemplo-verificado python -m unittest discover -s .
```

## Widgets / features

| Feature | Shape / nombre | Estado |
|---|---|---|
| Imagen estática | 30 | OK |
| Imagelist indexada | 31 | OK (verificado: weekday, batería 0–100) |
| Número digital | 32 | OK (verificado: día, hora, temp `2031`, AQI `5031`) |
| Agujas analógicas | 27 | OK (byte-exact + hardware) |
| AOD (`AOD/*.fprj` + `AOD/images/`) | subproyecto | OK |
| Varias `.fprj` en un directorio | multi-face | OK en packing; picker firmware **no verificado** |
| Animación nativa | `anim_[n@ms]` → kind4 | **OK en Band 9 real** |
| Atajo táctil | `btn_[destino]` + `Action_Code` → kind9 | **OK en Band 9 real** |
| `--share-resources` | CLI | OK (packing); semántica UI firmware **no verificada** |
| `--face-previews` | CLI | Empaqueta; firmware **ignora** — dejar apagado |
| Arco / progress | 29 / 42 | **Rechazado** |
| Apps | `app_` | **Rechazado** |
| Contenedores anidados | 34 | **Rechazado** |
| `Alpha` ≠ 255 / `Visible_Src` ≠ 0 | attrs | **Rechazado** |

## Fuentes de datos Band 9 (mínimo útil)

Usar solo tabla `xiaomi_band_9`. Códigos genéricos `xiaomi_color` (11/12/20/…)
leen como **0** en hardware.

| ID | Uso |
|---|---|
| `0811` / `1011` / `1811` | hora / minuto / segundo (agujas) |
| `1812` | día del mes |
| `2012` | semana **0=domingo … 6=sábado** |
| `0841` | batería % |
| `0821` | pasos |
| `2031` / `5031` | temperatura / AQI (probados en Band 9) |

Jump codes de `btn_`: ver [`AUTHORING.md`](AUTHORING.md) (tabla canónica). El
packer **no** lleva esa tabla a propósito; van en `Action_Code`.

## Docs conocidas como desfasadas

| Documento | Problema | Confiar en |
|---|---|---|
| `miband9-face-packer/docs/FORMAT.zh-CN.md` §9–10 | Cuerpo histórico marca anim/btn no implementados (hay note al inicio) | Este STATUS + código actual |
| `ejemplo-verificado/DETAILS.md` | Secciones internas aún hablan de Wine; hay banner monorepo al inicio | Banner + este STATUS; weekday `0=domingo` |

## Principios innegociables

1. **Fail closed**: shape/feature desconocido → error explícito, nunca silencioso.
2. **Solo Band 9** hasta existir un `DeviceProfile` real.
3. **Sin tabla de Action_Code en runtime** — tabla canónica en [`AUTHORING.md`](AUTHORING.md).
4. **Byte-exact del ejemplo** = gate de calidad del compilador.
