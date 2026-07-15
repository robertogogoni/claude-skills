# claude-skills

A collection of reusable Claude Code / agent skills, curated and maintained across machines.

## Skills

| Skill | What it does |
|-------|--------------|
| `claude-code-consolidate-speedrun` | Consolidate Claude Code to a single canonical install source (npm global) and fix startup slowness on Windows — disable unused plugins, remove dead MCP servers, pin MCP packages to avoid `npx` redownloads, lower effort level, and safely prune the plugins cache without touching memory stores. |

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
