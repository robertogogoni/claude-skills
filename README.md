# claude-skills

A collection of reusable Claude Code / agent skills, curated and maintained across machines.

## Skills

| Skill | What it does |
|-------|--------------|
| `claude-code-consolidate-speedrun` | Consolidate Claude Code to a single canonical install source (npm global) and fix startup slowness on Windows — disable unused plugins, remove dead MCP servers, pin MCP packages to avoid `npx` redownloads, lower effort level, and safely prune the plugins cache without touching memory stores. |
| `hermes-terminal-rendering` | Diagnose and fix flicker, scroll corruption, broken colors, and broken autocomplete when running the Hermes CLI (prompt_toolkit REPL) inside embedded / web-emulated terminals — Google Antigravity IDE, VS Code integrated terminal, any xterm.js web terminal. Covers the prompt_toolkit Windows backend bug and the `PROMPT_TOOLKIT_NO_CPR` fix, plus colored-division helpers (`cl`/`rule`/`section`). |

## Layout

```
skills/
  <skill-name>/
    SKILL.md
```

Each skill follows the standard Claude Code skill format (YAML frontmatter + markdown body).

## Adding a skill

1. Drop a folder under `skills/<skill-name>/` containing `SKILL.md`.
2. `git add . && git commit -m "add <skill-name>" && git push`
