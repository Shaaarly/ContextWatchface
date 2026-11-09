# Cómo funciona el context de este repo

Meta-documento del stack de context engineering. Obligaciones duras:
[`STATUS.md`](STATUS.md). Mapa de código: [`ARCHITECTURE.md`](ARCHITECTURE.md).

## Principio

La **prosa larga** vive solo en `docs/`. Las entradas de IDE (`AGENTS.md`,
`CLAUDE.md`) y las rules (`.cursor/rules/`, `.claude/rules/`) son delgadas:
recuerdan restricciones y apuntan aquí. Si algo diverge, **gana STATUS**.

## Qué lee cada herramienta

| Herramienta | Boot | Rules |
|---|---|---|
| Cursor | `AGENTS.md` + rules `.cursor/rules/*.mdc` | core siempre; packer/autoría por glob |
| Claude Code | `CLAUDE.md` + `.claude/rules/*.md` | mismo semántica que Cursor |
| Humano | [`../LEEME.md`](../LEEME.md) | — |

Cursor y Claude **deben** compartir las mismas obligaciones. No editar solo un
lado de las rules: al cambiar política, actualizar ambos espejos y el doc
canónico en `docs/`.

## Orden de lectura por tipo de tarea

| Tarea | Leer primero |
|---|---|
| Cualquiera (arranque en frío) | Este CONTEXT → [`STATUS.md`](STATUS.md) |
| Compilar / validar | [`QUICKSTART.md`](QUICKSTART.md) |
| Escribir o editar un `.fprj` | [`AUTHORING.md`](AUTHORING.md) |
| Tocar el compilador / codec | STATUS + [`ARCHITECTURE.md`](ARCHITECTURE.md) + código en `miband9-face-packer/` |
| Entender formato binario `.face` | `miband9-face-packer/docs/FORMAT.zh-CN.md` **cruzado con STATUS** |
| Diseño del ejemplo analógico | `ejemplo-verificado/` (banner: build = packer local) |

## Prioridad de fuentes de verdad

1. [`STATUS.md`](STATUS.md) — verificado / rechazado / SHA golden
2. Código actual en `miband9-face-packer/`
3. [`ARCHITECTURE.md`](ARCHITECTURE.md)
4. [`AUTHORING.md`](AUTHORING.md) / [`QUICKSTART.md`](QUICKSTART.md)
5. Satélites (`LEEME.md`, READMEs, `DETAILS.md`, FORMAT) — pueden estar viejos

## Qué archivo actualizar según el cambio

| Cambio | Actualizar |
|---|---|
| Nueva afirmación verificada o feature rechazada | `STATUS.md` (+ fila en AUTHORING si es de autoría) |
| Nuevo comando de uso | `QUICKSTART.md` (y resumen en LEEME si es usuario) |
| Nueva regla de `.fprj` / jump code | `AUTHORING.md` (no duplicar tabla en LEEME) |
| Fronteras de módulos / refactor | `ARCHITECTURE.md` |
| Política de agentes / IDE | `CONTEXT.md` + `AGENTS.md` + `CLAUDE.md` + ambos sets de rules |
| Solo UX usuario ES | `LEEME.md` |

## Rules: sincronía Cursor ↔ Claude

Pares espejo (mismo contenido semántico):

| Cursor | Claude |
|---|---|
| `.cursor/rules/watchface-core.mdc` | `.claude/rules/watchface-core.md` |
| `.cursor/rules/packer.mdc` | `.claude/rules/packer.md` |
| `.cursor/rules/authoring.mdc` | `.claude/rules/authoring.md` |

Los `.mdc` llevan frontmatter YAML de Cursor; los `.md` de Claude son markdown
plano. La política (Band 9, fail closed, byte-exact, sin Action_Code en
runtime) debe coincidir palabra por palabra en lo esencial.

## Orquestación / modo equipo (Claude Code)

Asume el plugin **everything-claude-code** ya instalado en el entorno del
usuario. No inventar agents nuevos: los nombres de abajo son **roles /
aliases** de agents del plugin.

### Rules vs agents/commands

| Mecanismo | ¿Se aplica solo? |
|---|---|
| Rules (`.claude/rules/`, `.cursor/rules/`) | **Sí** — contexto persistente |
| Agents / commands del plugin (`/orchestrate`, `/plan`, …) | **No** — hay que invocarlos o lanzar el agent |

El agente principal actúa como **tech lead**: en tareas no triviales **debe
orquestar** subagentes; no implementar solo.

### Umbral trivial vs orquestar

| Trivial (respuesta o cambio directo) | Orquestar (obligatorio) |
|---|---|
| Pregunta de lectura / aclaración | Feature nueva o cambio de comportamiento |
| Typo o corrección de **1 línea** | Bugfix con diagnóstico |
| Señalar un link roto sin más | Refactor de módulos / fronteras |
| | Cambio de política en STATUS/docs/rules |
| | Fallos de build/tests que no sean un typo obvio |

### Workflows

| Tipo | Cadena |
|---|---|
| **feature** | `planner` → `tdd-guide` → `code-reviewer` → (`security-reviewer` solo si hay auth/red/secretos) → `doc-updater` si toca STATUS/docs/rules |
| **bugfix** | explorer/`planner` → `tdd-guide` → `code-reviewer` |
| **refactor** | `architect` → `tdd-guide` → `code-reviewer` |
| **docs** | `doc-updater` (+ `code-reviewer` si cambia política de agentes o contrato) |

Si fallan tests/build a mitad: `build-error-resolver`, luego retomar la cadena.

### Commands útiles (plugin)

- `/orchestrate feature|bugfix|refactor|security|custom`
- `/plan` · `/tdd` · `/code-review` · `/verify`

Preferir `/orchestrate …` o lanzar agents con **handoff** explícito.

### Handoff obligatorio entre agents

Cada traspaso incluye:

1. **Context** — objetivo y restricciones del repo aplicables
2. **Findings** — lo ya descubierto
3. **Files** — rutas tocadas o a tocar
4. **Open Questions** — bloqueos / decisiones pendientes
5. **Recommendations** — siguiente paso concreto

### Roles del equipo (alias → responsabilidad)

| Rol | Agent | Responsabilidad |
|---|---|---|
| PM / tech lead (plan) | `planner` | Descomponer trabajo; no codear de más |
| Arquitectura | `architect` | Fronteras del monorepo; capas; DeviceProfile futuro |
| Implementación + tests | `tdd-guide` | Código con tests; respetar byte-exact |
| Calidad | `code-reviewer` | Maintainability, fail closed, sin scope creep |
| Seguridad | `security-reviewer` | Solo auth/red/secretos (raro en este repo) |
| Build/tests rotos | `build-error-resolver` | Desbloquear CI/local unittest |
| Docs / context | `doc-updater` | STATUS, AUTHORING, CONTEXT, rules Cursor↔Claude |

### Restricciones duras en toda orquestación

Igual que el resto del context: solo Band 9; fail closed; no romper SHA
golden; no tabla `Action_Code` en runtime; no `compile.exe`; no flashear.
Detalle: [`STATUS.md`](STATUS.md).
