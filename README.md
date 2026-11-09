# ContextWatchface

Kit **open source** para crear watch faces de **Xiaomi Smart Band 9**
(`DeviceType=366`, 192×490): compilador Python (`.fprj` + `images/` → `.face`)
más una capa de **context engineering** lista para Cursor y Claude Code.

> Alcance actual: **solo Band 9**. Band 8/10 y apps como Notify quedan fuera
> hasta existir un `DeviceProfile` documentado en [`docs/STATUS.md`](docs/STATUS.md).

## Qué incluye

| Pieza | Rol |
|---|---|
| [`miband9-face-packer/`](miband9-face-packer/) | Compilador + codec RLE + validación Gadgetbridge |
| [`ejemplo-verificado/`](ejemplo-verificado/) | Proyecto golden (byte-exact vs `AnalogFull.face`) |
| [`docs/`](docs/) | Contrato, autoría, arquitectura, cómo usar el context |
| [`AGENTS.md`](AGENTS.md) / [`CLAUDE.md`](CLAUDE.md) | Boot para agentes (Cursor / Claude) |
| [`.cursor/rules/`](.cursor/rules/) · [`.claude/rules/`](.claude/rules/) | Rules IDE (espejo) |
| [`LEEME.md`](LEEME.md) | Guía rápida en español |

Basado en [brigealong/miband9-face-packer](https://github.com/brigealong/miband9-face-packer) (MIT)
con parches locales (`anim_`, `btn_`, `--share-resources`, …). Ver STATUS.

## Requisitos

- Python ≥ 3.10
- Pillow: `pip install Pillow`

## Arranque rápido (humano)

```bash
git clone https://github.com/Shaaarly/ContextWatchface.git
cd ContextWatchface/miband9-face-packer
python make_minimal.py
python pack_face.py samples/minimal probe.face --id 123456789
python validate_gb.py probe.face
```

Detalle: [`docs/QUICKSTART.md`](docs/QUICKSTART.md). Autoría `.fprj`: [`docs/AUTHORING.md`](docs/AUTHORING.md).

## Cómo usar el context (agentes / IA)

Este repo está pensado para clonarlo y trabajar con **Cursor** o **Claude Code**
sin redescubrir reglas a mano.

### 1. Orden de lectura (arranque en frío)

1. [`docs/CONTEXT.md`](docs/CONTEXT.md) — cómo está montado el stack  
2. [`docs/STATUS.md`](docs/STATUS.md) — **fuente de verdad #1** (qué funciona / qué no)  
3. Según la tarea:
   - compilar → QUICKSTART  
   - escribir `.fprj` → AUTHORING  
   - tocar el packer → ARCHITECTURE + código  

Si un README o comentario contradice **STATUS**, gana STATUS.

### 2. Cursor

- Al abrir el repo, Cursor carga [`AGENTS.md`](AGENTS.md) y
  [`.cursor/rules/`](.cursor/rules/) (`watchface-core` siempre; packer/autoría por glob).
- No hace falta pegar el context en el chat: apunta al agente a `docs/CONTEXT.md`
  o deja que las rules lo enlacen.

### 3. Claude Code

- Boot: [`CLAUDE.md`](CLAUDE.md) + [`.claude/rules/`](.claude/rules/) (mismo contrato que Cursor).
- **Modo equipo**: en tareas no triviales el agente debe orquestar subagentes
  (plugin [everything-claude-code](https://github.com/affaan-m/everything-claude-code)
  si lo tienes instalado): `/orchestrate`, `/plan`, `/tdd`, `/code-review`, …
- Detalle de roles, workflows y handoffs: sección *Orquestación* en
  [`docs/CONTEXT.md`](docs/CONTEXT.md).

### 4. Política corta (no negociable)

- Solo Band 9 hasta nuevo acuerdo en STATUS  
- Fail closed: feature desconocida → error, nunca drop silencioso  
- No romper el SHA golden del ejemplo verificado  
- No meter tabla de `Action_Code` en el runtime (va en AUTHORING)  
- No ejecutar `compile.exe` ni flashear desde el toolchain  

### 5. Tras cambiar packing / codec

```bash
cd miband9-face-packer
MINIMAL_ANALOG_DIR=../ejemplo-verificado python -m unittest discover -s .
```

## Mapa de docs

| Doc | Para qué |
|---|---|
| [docs/CONTEXT.md](docs/CONTEXT.md) | Meta-context + orquestación Cursor↔Claude |
| [docs/STATUS.md](docs/STATUS.md) | Verificado / rechazado / SHA |
| [docs/QUICKSTART.md](docs/QUICKSTART.md) | Comandos mínimos |
| [docs/AUTHORING.md](docs/AUTHORING.md) | Widgets, sources, `anim_`/`btn_`, jump codes |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Capas y fronteras del código |
| [LEEME.md](LEEME.md) | Guía usuario ES |

## Instalación en la banda

Fuera del compilador. Camino documentado: [Gadgetbridge](https://gadgetbridge.org/)
→ Instalar fichero → el `.face`. Usa un ID de 9 dígitos distinto por esfera.
Instalar esferas de terceros es bajo tu responsabilidad.

## Licencia

El packer y este kit siguen la licencia MIT del upstream (`miband9-face-packer/LICENSE`).
El ejemplo verificado proviene de [Vadim170/miband9-minimal-analog](https://github.com/Vadim170/miband9-minimal-analog).
