# Kit para hacer watch faces de Xiaomi Smart Band 9

Compila un proyecto Mi Create (`.fprj` + `images/`) a un `.face` instalable,
**sin Windows, sin Wine y sin el `compile.exe` cerrado** que pide Mi Create.

Solo necesitas **Python >= 3.10 y Pillow** (`pip install Pillow`).

## Context engineering (agentes y contribuidores)

| Doc | Para qué |
|---|---|
| [`docs/CONTEXT.md`](docs/CONTEXT.md) | Cómo funciona el stack de contexto |
| [`AGENTS.md`](AGENTS.md) | Entrada Cursor / agentes genéricos |
| [`CLAUDE.md`](CLAUDE.md) | Entrada Claude Code |
| [`docs/STATUS.md`](docs/STATUS.md) | Qué está verificado / rechazado |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Mapa del repo y fronteras de código |
| [`docs/AUTHORING.md`](docs/AUTHORING.md) | Autoría `.fprj` + jump codes `btn_` |
| [`docs/QUICKSTART.md`](docs/QUICKSTART.md) | Comandos mínimos |
| [`.cursor/rules/`](.cursor/rules/) / [`.claude/rules/`](.claude/rules/) | Rules IDE (espejo) |

Si un README o comentario contradice `docs/STATUS.md`, gana STATUS.

## Empieza aqui

Copia operativa canónica: [`docs/QUICKSTART.md`](docs/QUICKSTART.md).

```bash
cd miband9-face-packer
python make_minimal.py                                  # crea un proyecto de prueba
python pack_face.py samples/minimal probe.face --id 123456789
python validate_gb.py probe.face                        # debe decir PASS
```

Eso ya es un `.face` instalable. A partir de ahi, cambia los PNG de
`samples/minimal/images/` y las coordenadas del `.fprj`.

`ejemplo-verificado/` es un proyecto publico completo
([Vadim170/miband9-minimal-analog](https://github.com/Vadim170/miband9-minimal-analog))
que ya se sabe que funciona en una Band 9 real: agujas analogicas, AOD y un
segundo `.fprj`. Es la mejor referencia de como se monta uno de verdad.

```bash
python pack_face.py ../ejemplo-verificado salida.face --id 167210065
python inspect_face.py salida.face        # lo desmonta entero y verifica cada frame
```

Ese `salida.face` sale **byte a byte identico** al `AnalogFull.face` que
viene en la carpeta y que compilo el compilador original. Si te da el mismo
`sha256`, tu instalacion esta bien.

## Que tiene de especial esta copia

Es [brigealong/miband9-face-packer](https://github.com/brigealong/miband9-face-packer)
(MIT) **con cuatro parches**. Si lo bajas de GitHub no los tienes:

| | |
|---|---|
| `anim_[n@ms]` | animacion nativa `kind4`. La unica forma de pasar del techo de 1 Hz que imponen las fuentes de datos. **Verificado en una Band 9 real** |
| `btn_[destino]` | accesos directos tactiles `kind9`: tocas un sitio del dibujo y se abre una app. **Verificado en una Band 9 real** |
| `--share-resources` | varias faces en un fichero compartiendo pixeles (de 610 KB por estilo a ~1 KB) |
| `--face-previews` | previsualizacion por face. Probado: el firmware la ignora. Se queda apagado |

Detalle de autoría (`btn_`, `anim_`, sources): [`docs/AUTHORING.md`](docs/AUTHORING.md).

La suite de tests incluye uno que reconstruye el proyecto publico y exige el
fichero byte a byte identico:

```bash
MINIMAL_ANALOG_DIR=../ejemplo-verificado python -m unittest discover -s .
```

## Accesos directos tactiles

Un `btn_` es un Shape 30 con nombre `btn_[destino]` y el codigo en
`Action_Code`, colocado encima del dibujo que quieras que sea el boton. El
PNG que referencia va **totalmente transparente**: es solo el rectangulo de
impacto. Ponlo **el ultimo** de la lista de widgets.

```xml
<Widget Shape="30" Name="btn_[timer]" X="70" Y="68" Width="90" Height="88"
        Alpha="255" Visible_Src="0" Bitmap="btn_face.png"
        Action_Code="010C6F02" />
```

El packer **no lleva** la tabla de codigos a proposito. La tabla canónica de
jump codes está en [`docs/AUTHORING.md`](docs/AUTHORING.md).

## Lo que necesitaras ademas

- **[Mi-Create](https://github.com/ooflet/Mi-Create)** — el editor oficioso. No
  hace falta para compilar, pero su `src/data/sources.json` es **la** tabla de
  fuentes de datos. Clonalo tu, son 46 MB.
- **[Gadgetbridge](https://gadgetbridge.org/)** para instalar:
  *Dispositivo -> menu -> Instalar fichero -> el `.face` o `.bin`*.

## Avisos, por orden de cuanto duelen

- Solo Band 9, `DeviceType="366"`, **192x490**. El packer rechaza lo demas.
- Instalar esferas de terceros es bajo tu responsabilidad. Gadgetbridge avisa
  de que una esfera de **otro** modelo puede inutilizar el reloj.
- Usa un **id de 9 digitos distinto** por esfera o se pisan entre ellas.
- El movil **cachea la previsualizacion contra ese id**. Si recompilas con el
  mismo id puede seguir ensenandote la imagen vieja.
- El panel es AMOLED: el negro es *apagado*.
- Los fotogramas son RLE: **el color plano es casi gratis, un degradado cuesta
  cuatro bytes por pixel**.
- La fuente del dia de la semana (`2012`) es **0=domingo**.

MIT, de brigealong. El `LICENSE` va dentro.
