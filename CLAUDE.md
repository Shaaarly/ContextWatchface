# CLAUDE.md — boot Claude Code

Lee primero [`docs/CONTEXT.md`](docs/CONTEXT.md) y [`docs/STATUS.md`](docs/STATUS.md).
Workflows compartidos (no duplicar aquí): [`AGENTS.md`](AGENTS.md).

## Modo equipo (obligatorio)

Detalle canónico: [`docs/CONTEXT.md`](docs/CONTEXT.md) → *Orquestación / modo equipo*.

- Actúas como **tech lead**: en tareas **no triviales** orquesta subagentes;
  **no implementes solo**.
- Preferir `/orchestrate feature|bugfix|refactor|security|custom` o lanzar
  agents del plugin **everything-claude-code** con **handoff**
  (Context / Findings / Files / Open Questions / Recommendations).
- **Excepción trivial:** pregunta de lectura o typo de 1 línea → directo.
- Commands útiles: `/plan`, `/tdd`, `/code-review`, `/verify`.
- Toda cadena respeta restricciones duras (Band 9, fail closed, byte-exact,
  sin Action_Code en runtime, sin compile.exe / flasheo).

## Qué es

Toolchain **`.fprj` + `images/` → `.face`** para **Xiaomi Smart Band 9**
(`DeviceType="366"`, 192×490). Packer: `miband9-face-packer/`. Golden:
`ejemplo-verificado/`.

## Restricciones duras (iguales que AGENTS)

1. Solo Band 9 hasta existir `DeviceProfile` + fila en STATUS.
2. Fail closed: feature desconocida → error, nunca drop silencioso.
3. No romper byte-exact del ejemplo (SHA en STATUS).
4. No meter tabla de `Action_Code` en el código; jump codes en [`docs/AUTHORING.md`](docs/AUTHORING.md).
5. No ejecutar ni embeber `compile.exe` / DLLs decompiladas.
6. No flashear dispositivos desde el toolchain.

## Rules de este repo

Aplica también [`.claude/rules/`](.claude/rules/) (espejo de `.cursor/rules/`):

- `watchface-core.md` — siempre
- `packer.md` — al tocar el compilador
- `authoring.md` — al tocar `.fprj` / ejemplo

Si cambias política, actualiza **también** el par `.cursor/rules/*.mdc` y el doc en `docs/`.

## Lectura por tarea

| Tarea | Docs |
|---|---|
| Compilar / validar | [`docs/QUICKSTART.md`](docs/QUICKSTART.md) |
| Autoría `.fprj` | [`docs/AUTHORING.md`](docs/AUTHORING.md) |
| Packer / codec | STATUS + [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) |
| Formato binario | `miband9-face-packer/docs/FORMAT.zh-CN.md` cruzado con STATUS |

## Comandos de anclaje

```bash
cd miband9-face-packer
python make_minimal.py
python pack_face.py samples/minimal probe.face --id 123456789
python validate_gb.py probe.face

python pack_face.py ../ejemplo-verificado salida.face --id 167210065
MINIMAL_ANALOG_DIR=../ejemplo-verificado python -m unittest discover -s .
```

## Fuera de alcance

Band 8/10, Notify, arcs 29/42, `app_`, UI editor. Ver STATUS.
