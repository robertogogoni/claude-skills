---
name: claude-code-consolidate-speedrun
description: Consolidate Claude Code to a single canonical install source AND fix startup slowness on Windows. Use when Claude Code is launched from multiple places (npm + stray standalone claude.exe), feels slow to start, or when ~/.claude is bloated. Covers finding duplicate installs, removing the standalone binary, pinning the npm global source in PATH for every terminal/IDE/agent, disabling unused plugins (esp. LSP language-servers), removing dead MCP servers (e.g. Docker), pinning MCP packages to avoid npx redownloads, lowering effort level, and SAFELY pruning the plugins cache without touching memory stores.
---

# Claude Code: Consolidate to One Source + Speedrun

## When to use
- `which -a claude` shows more than one result (e.g. a standalone `~/.local/bin/claude.exe` AND an npm global).
- Claude Code launches slowly / hangs at startup.
- `~/.claude` directory is large (GBs) and you want it trimmed.
- User wants one "official, recommended, up-to-date" Claude Code invoked identically from any terminal, IDE, or agent.

## Critical gotcha (learned the hard way)
- **The `plugins/cache/` dir is NOT a pure download cache.** Enabled plugins' actual
  code lives there (e.g. `cache/superpowers-marketplace/superpowers/6.1.1`). A blanket
  `rm -rf plugins/cache` will BREAK enabled plugins. Prune TARGETED: disabled-plugin
  dirs + `temp_git_*` clones only.
- **`episodic-memory` and `claude-mem` plugins are the biggest folders (1+ GB).** These
  are the user's cross-machine MEMORY archives. Do NOT delete them even though large.
- **`security/agent-sdk-venv` is a standalone, regenerable Python venv** (Lib/Scripts/
  pyvenv.cfg), referenced by no config — safe to delete (frees ~310 MB).
- MCP servers defined as `npx -y @modelcontextprotocol/server-xyz` RE-DOWNLOAD on every
  cold launch → slow. Install them globally once and point the server `args` at the
  cached node_modules entry point instead.
- The standalone `claude.exe` (251 MB) does NOT auto-update. The npm global package does.
  Remove the standalone so `claude` resolves to npm everywhere.

## Step-by-step

### 1. Locate all installs
```bash
which -a claude
# also check the usual standalone spot:
ls -la "$HOME/.local/bin/claude"* 2>/dev/null
claude --version   # before
```

### 2. Install the canonical npm global (auto-updating)
```bash
npm install -g @anthropic-ai/claude-code
claude --version   # after — should be >= before
```
The npm shim lands in `C:/Users/<user>/AppData/Roaming/npm/claude` (Windows).

### 3. Remove the standalone binary
```bash
rm -f "$HOME/.local/bin/claude.exe"
```

### 4. Pin the npm bin FIRST in PATH (so claude resolves identically in every
###    terminal / IDE / agent). Add to ~/.bashrc:
```bash
case ":$PATH:" in
  *":/c/Users/rober/AppData/Roaming/npm:"*) ;;
  *) export PATH="/c/Users/rober/AppData/Roaming/npm:$PATH" ;;
esac
alias claude-update='npm update -g @anthropic-ai/claude-code && claude --version'
```
Verify in a clean login shell: `bash -lc 'which claude'` → `.../Roaming/npm/claude`.

### 5. Find what's actually slow (diagnose, don't guess)
```bash
du -sh "$HOME/.claude"                      # overall bloat
du -sh "$HOME/.claude"/* | sort -rh | head  # biggest subdirs
# enabled plugin count + which are unused:
grep -c '"[^"]*@[^"]*": true' "$HOME/.claude/settings.json"
# actual plugin usage from .claude.json:
grep -oE '"[a-z0-9@/-]+":\{"usageCount":[1-9][0-9]*' "$HOME/.claude.json"
# MCP servers (any needing Docker / npx redownload?):
#   look at "mcpServers" in $HOME/.claude.json
docker info >/dev/null 2>&1 && echo "docker up" || echo "docker DOWN"
```

### 6. Disable unused plugins (the #1 speed win)
- Read `enabledPlugins` in `~/.claude/settings.json`; keep only `usageCount > 0`.
- Especially disable all LSP language-servers you don't use
  (`typescript-lsp`, `pyright-lsp`, `rust-analyzer-lsp`, `gopls-lsp`, `csharp-lsp`,
  `kotlin-lsp`, `ruby-lsp`, `php-lsp`, `lua-lsp`, `swift-lsp`, `jdtls-lsp`, `clangd-lsp`)
  — each spawns a background process at startup.
- Set `effortLevel` from `high` to `medium` (faster responses).

### 7. Fix MCP servers (the #2 win)
- Remove servers that need a service not running (e.g. `MCP_DOCKER` when Docker is down →
  startup hang/retry).
- Pin `npx -y` servers to globally-installed packages:
  ```bash
  npm install -g @modelcontextprotocol/server-memory @modelcontextprotocol/server-filesystem
  # find entry points:
  find "$APPDATA/npm/node_modules/@modelcontextprotocol/server-memory" -name index.js -path "*dist*"
  ```
  Then edit `~/.claude.json` `mcpServers` `args` to point at those absolute paths.
- Always validate both JSON files after editing:
  ```bash
  python -c "import json;json.load(open(r'C:\Users\rober\.claude\settings.json'))"
  python -c "import json;json.load(open(r'C:\Users\rober\.claude.json'))"
  ```

### 8. SAFE cache prune (targeted only)
Use a script that:
- removes every `temp_git_*` dir under `plugins/cache/`,
- removes each `<marketplace>/<plugin>` dir whose key `<plugin>@<marketplace>` is NOT in
  the enabled-true set,
- removes `security/agent-sdk-venv` (regenerable).
Never delete the enabled-plugin dirs or the memory-plugin stores.
Re-check: `du -sh "$HOME/.claude/plugins/cache"` and confirm the enabled plugins' dirs
still exist.

## Verification (end-to-end)
```bash
bash -lc 'which claude; claude --version'          # single npm source
grep -c '"[^"]*@[^"]*": true' "$HOME/.claude/settings.json"   # = number kept
grep -c MCP_DOCKER "$HOME/.claude.json"            # = 0
grep '"effortLevel"' "$HOME/.claude/settings.json" # medium
```
Then **quit and relaunch Claude Code** — it should start faster with fewer
background processes.

## Pitfalls
- MSYS paths like `/c/Users/...` do NOT resolve in Python — use native
  `r"C:\Users\..."` or `C:/Users/...`.
- Don't keep a startup hook unless needed; a `node` `UserPromptSubmit` hook adds
  ~440 ms per prompt (usually acceptable, leave unless profiling says otherwise).
- CLAUDE.md size is rarely the slowness cause (here it was 14 KB); don't blame memory
  files first — profile `plugins/`, `mcpServers`, and `effortLevel`.
