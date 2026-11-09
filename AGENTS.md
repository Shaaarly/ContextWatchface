# AGENTS — context engineering

Lee primero [`docs/CONTEXT.md`](docs/CONTEXT.md) y [`docs/STATUS.md`](docs/STATUS.md).
Mapa de código: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

**Claude Code** usa [`CLAUDE.md`](CLAUDE.md) como boot; las obligaciones son las
mismas. No diverjas políticas entre `AGENTS.md` y `CLAUDE.md` ni entre
`.cursor/rules/` y `.claude/rules/`.

## Modo equipo / orquestación

Misma política en Cursor y Claude: el agente principal es **tech lead**.
Tareas no triviales → orquestar (plugin everything-claude-code: `/orchestrate`,
agents `planner` / `architect` / `tdd-guide` / `code-reviewer` / …) con handoff
estructurado. Trivial (pregunta o typo 1 línea) → directo. Roles, workflows y
commands: [`docs/CONTEXT.md`](docs/CONTEXT.md) (*Orquestación / modo equipo*).
No duplicar aquí la tabla de agents.

## Qué es este proyecto

Toolchain **Mi Create `.fprj` + `images/` → `.face` instalable** para
**Xiaomi Smart Band 9** (`DeviceType="366"`, 192×490), en Python puro
(Pillow), sin `compile.exe` / Wine.

- Compilador: `miband9-face-packer/`
- Golden sample: `ejemplo-verificado/` (byte-exact vs `AnalogFull.face`)
- Guía usuario ES: `LEEME.md`
- Autoría: [`docs/AUTHORING.md`](docs/AUTHORING.md)
- Arranque: [`docs/QUICKSTART.md`](docs/QUICKSTART.md)

## Restricciones duras

1. **Solo Band 9.** No ampliar a Band 8/10 ni otros `DeviceType` sin un
   `DeviceProfile` explícito y acuerdo en STATUS.
2. **Fail closed.** Shape, nombre especial o attr no soportado → error;
   nunca omitir en silencio.
3. **No romper byte-exact** del ejemplo (`docs/STATUS.md` → SHA-256).
4. **No meter tabla de `Action_Code` en el código** — jump codes en
   [`docs/AUTHORING.md`](docs/AUTHORING.md).
5. **No ejecutar / embeber** `compile.exe` ni DLLs decompiladas.
6. Instalación en dispositivo y apps (Notify, Mi Fitness) **no** son parte
   del compilador; documentar avisos de riesgo, no flashear desde aquí.

## Fuentes de verdad (prioridad)

1. `docs/STATUS.md` — qué está verificado / rechazado
2. Código actual en `miband9-face-packer/`
3. `docs/ARCHITECTURE.md` — fronteras y plan de capas
4. `docs/AUTHORING.md` / `docs/QUICKSTART.md`
5. `LEEME.md` — guía usuario ES
6. `miband9-face-packer/docs/FORMAT.zh-CN.md` — layout binario; **cruzar
   con STATUS** si habla de anim/btn “no implementados”

Si un comentario de código o un README satélite contradice STATUS, gana STATUS
y hay que alinear el texto desfasado.

## Workflows

| Tipo de tarea | Leer | Hacer |
|---|---|---|
| Packer / codec | STATUS + ARCHITECTURE + código | Mantener CLI; fail closed; tests abajo |
| Nueva / editar cara | AUTHORING + QUICKSTART + ejemplo | `DeviceType=366`; sources Band 9; no editar golden a mano |
| Docs / context | CONTEXT | Actualizar STATUS si cambia una afirmación verificada; sincronizar rules Cursor↔Claude |
| Formato `.face` | FORMAT + STATUS | No reintroducir “anim/btn no implementados” |

Tras tocar packing o codec:

```bash
cd miband9-face-packer
MINIMAL_ANALOG_DIR=../ejemplo-verificado python -m unittest discover -s .
```

## Comandos de anclaje

Ver también [`docs/QUICKSTART.md`](docs/QUICKSTART.md).

```bash
cd miband9-face-packer
python make_minimal.py
python pack_face.py samples/minimal probe.face --id 123456789
python validate_gb.py probe.face

python pack_face.py ../ejemplo-verificado salida.face --id 167210065
python inspect_face.py salida.face

MINIMAL_ANALOG_DIR=../ejemplo-verificado python -m unittest discover -s .
```

## Fuera de alcance (por ahora)

- Soporte Band 8 / 10 / Redmi Watch
- Integración Notify
- Progress arcs (29/42), `app_`, contenedores anidados
- Editor visual / UI
- Prometer que `--face-previews` o multi-face picker funcionan en firmware
