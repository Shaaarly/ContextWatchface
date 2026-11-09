# WatchFace — reglas globales

Antes de cambiar código o docs, lee `docs/CONTEXT.md`, `AGENTS.md` o `CLAUDE.md`, y `docs/STATUS.md`.

## Alcance

- Objetivo: `.fprj` + `images/` → `.face` para **Smart Band 9** (`DeviceType=366`, 192×490).
- Band 8/10, Notify y otros dispositivos: **fuera de alcance** hasta `DeviceProfile` + STATUS.
- No ejecutar ni redistribuir `compile.exe` / ensamblados decompilados.

## Contrato

- Fail closed: features desconocidas → `ValueError`, nunca drop silencioso.
- No romper byte-exact de `ejemplo-verificado` (SHA en `docs/STATUS.md`).
- No meter tabla de jump codes `Action_Code` en runtime; solo en `docs/AUTHORING.md`.

## Fuentes de verdad

1. `docs/STATUS.md`
2. Código en `miband9-face-packer/`
3. `docs/ARCHITECTURE.md`
4. Si `FORMAT.zh-CN.md` o comentarios viejos contradicen STATUS (p. ej. anim/btn), gana STATUS.

## Orquestación

Tareas no triviales: orquestar subagentes (tech lead), no implementar solo.
Trivial = pregunta / typo 1 línea. Detalle: `docs/CONTEXT.md` (*Orquestación*).
Asume plugin everything-claude-code; preferir `/orchestrate` + handoffs.

## Sync

Espejo de `.cursor/rules/watchface-core.mdc`. Al cambiar política, actualizar ambos.
