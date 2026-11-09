# Autoría de watch faces (`.fprj`)

Canónico para escribir proyectos Mi Create compatibles con este packer.
Estado de soporte: [`STATUS.md`](STATUS.md). Arranque: [`QUICKSTART.md`](QUICKSTART.md).

## Dispositivo

```xml
<FaceProject DeviceType="366" Id="167210065">
  <Screen Title="Mi cara" Bitmap="preview.png">
    <!-- widgets -->
  </Screen>
</FaceProject>
```

- Solo `DeviceType="366"` (Band 9, 192×490). Cualquier otro valor lo rechaza el packer.
- Imágenes relativas a `images/` (PNG). Preview en `Screen/@Bitmap`.
- AOD opcional: carpeta `AOD/` con un único `AOD/*.fprj` y `AOD/images/`.

## Widgets soportados

Orden en el XML = **z-order** (el último se dibuja encima).

| Shape | Tipo | Notas |
|---|---|---|
| 30 | Imagen estática | `Bitmap` |
| 31 | Imagelist | `BitmapList` con `(N):file.png`, `Index_Src` |
| 32 | Número digital | `BitmapList` `0.png\|…\|9.png`, `Value_Src`, `Digits`, `Alignment`, `Blanking`, `Spacing` |
| 27 | Analógico | hasta 3 agujas; el packer las expande a elementos |

Rechazados (fail closed): 29/42 progress, `app_`, contenedores anidados, `Alpha`≠255, `Visible_Src`≠0.

### Imagelist (31)

```text
BitmapList="(0):wd_0.png|(1):wd_1.png|…"
```

Sin prefijos `(N):` el compilador original / este packer fallan.

### Número (32)

`Alignment`: 0=Left, 1=Center, 2=Right. `Blanking=1` oculta ceros a la izquierda.

### Analógico (27)

Pivotes `*Image_rotate_xc/yc` en px dentro de la imagen de la aguja. Sources fijos
de aguja: hora `0811`, minuto `1011`, segundo `1811`.

## Fuentes de datos Band 9

Usar solo la tabla `xiaomi_band_9` (p. ej. en Mi Create `sources.json`). Los
códigos genéricos `xiaomi_color` (11/12/20/…) leen como **0** en hardware.

| ID | Uso |
|---|---|
| `0811` / `1011` / `1811` | hora / minuto / segundo (agujas) |
| `1812` | día del mes |
| `2012` | semana **0=domingo … 6=sábado** |
| `0841` | batería % |
| `0821` | pasos |
| `0822` | pulso |
| `0823` | calorías |
| `1012` | mes (**no probado en hardware**; base asumida 1) |
| `2031` / `5031` | temperatura / AQI (probados en Band 9) |

Tabla completa de referencia: clonar [Mi-Create](https://github.com/ooflet/Mi-Create) → `src/data/sources.json`.

## Animación nativa `anim_[n@ms]`

Única vía práctica por encima del techo ~1 Hz de las fuentes de datos.
Verificado en Band 9 real (kind4).

- Nombre: `anim_[count@delay]` — `count` = frames, `delay` = ms entre frames.
- `BitmapList` con exactamente `count` PNG (mismo tamaño).
- Diseñar con colores planos / cajas recortadas (RLE).

## Atajos táctiles `btn_[destino]`

Verificado en Band 9 real (kind9).

- Shape **30**, nombre `btn_[destino]` (destino solo etiqueta).
- `Action_Code`: exactamente **8 hex** (el packer **no** lleva la tabla).
- Opcional `Action_Tag`: 4 hex (marker; default `0000`).
- PNG **totalmente transparente** (solo hit-area); si pintas, tapas lo de debajo.
- Colocar **al final** de la lista de widgets.

```xml
<Widget Shape="30" Name="btn_[timer]" X="70" Y="68" Width="90" Height="88"
        Alpha="255" Visible_Src="0" Bitmap="btn_face.png"
        Action_Code="010C6F02" />
```

### Jump codes (canónico)

Origen: exportador Mi Create `.fprj`→wfDef / [Pzqqt/Fprj_to_wfDef](https://github.com/Pzqqt/Fprj_to_wfDef) `exporter.py`.

| destino | codigo |
|---|---|
| `alarm` | `010C8F02` |
| `alexa` | `010CDF02` |
| `calories` | `03033F01` |
| `cards` | `010ABF02` |
| `contact` | `010CEF02` |
| `flashlight` | `010CAF01` |
| `hrm` | `03065F00` |
| `moving` | `03053F01` |
| `music` | `010C5F01` |
| `phone` | `010C3F02` |
| `photo` | `010CCF01` |
| `sleep` | `0300CF00` |
| `spo2` | `0307EF00` |
| `standing` | `03043F01` |
| `steps` | `03023F01` |
| `stopwatch` | `010C0F02` |
| `stress` | `03083F00` |
| `timer` | `010C6F02` |
| `voice` | `010C9F02` |
| `weather` | `030B1F02` |

## Pitfalls

- **ID de 9 dígitos** distinto por esfera; el móvil cachea preview por ID.
- AMOLED: negro = píxel apagado; una placa negra “no se ve”.
- RLE: color plano barato; degradado ≈ 4 bytes/píxel.
- Semana `2012`: base **0=domingo**. Lista lunes-primero falla solo en domingo.
- No editar `ejemplo-verificado/AnalogFull.face` a mano: recompilar con el packer.
- `tools/build_sim.py` del ejemplo está desfasado: no regenerar `simulator.html` con él.

## Referencia de proyecto

`ejemplo-verificado/` — analógico + AOD + golden `.face`. Diseño detallado histórico
en `ejemplo-verificado/DETAILS.md` (leer el banner: build canónico = este packer).
