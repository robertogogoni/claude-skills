---
name: hermes-terminal-rendering
description: Diagnose and fix flicker, scroll corruption, broken colors, and broken autocomplete when running the Hermes CLI (the classic prompt_toolkit REPL) inside embedded or web-emulated terminals — Google Antigravity IDE, VS Code integrated terminal, any xterm.js-based web terminal, WSL, tmux, ConEmu. Covers the prompt_toolkit Windows backend-selection bug and the PROMPT_TOOLKIT_NO_CPR fix.
---

# Hermes Terminal Rendering Fixes (embedded / web-emulated terminals)

## When to use
- User reports the Hermes CLI "flickers", "doesn't render correctly when scrolling", garbled/duplicated output, wrong colors, or an autocomplete menu that looks broken.
- The terminal is non-standard: Antigravity IDE, VS Code integrated terminal, any xterm.js web terminal, WSL, tmux, ConEmu, etc.
- "Gravity IDE" / "Antigravity" == Google Antigravity IDE; its terminal emulates VS Code xterm.js (`TERM_PROGRAM=vscode`).

## Root cause (the real bug)
Hermes CLI renders through prompt_toolkit (a `full_screen=False` `Application` + `patch_stdout`). On Windows (`sys.platform == "win32"`) `create_output()` chooses its backend by calling `is_win_vt100_enabled()`, which opens the REAL Windows console handle (`GetConsoleMode`/`SetConsoleMode`) and tries to enable VT processing. In a web-emulated terminal (xterm.js with no real conhost) that probe returns `False`, so prompt_toolkit falls back toward `Win32Output`, which raises `NoConsoleScreenBufferError` and degrades the renderer. The degraded path also emits Cursor Position Report queries (`ESC[6n`); over a web PTY those replies round-trip badly → flicker + scroll corruption. Autocomplete menus and color styling ride the same broken renderer, so they look wrong too.

CRITICAL: prompt_toolkit ignores `TERM`/`COLORTERM` for backend selection — it probes the conhost directly. So setting `TERM` alone does NOT fix it.

## Diagnosis (reproduce first — never guess)
1. Identify the terminal: `echo "$TERM_PROGRAM $TERM $COLORTERM"`. `vscode` ⇒ xterm.js.
2. Probe the backend selection Hermes will hit (see `scripts/probe_rendering.py` for a re-runnable version):
   ```bash
   python - <<'PY'
   import sys, os
   from prompt_toolkit.output.windows10 import is_win_vt100_enabled
   from prompt_toolkit.output.defaults import create_output
   print("is_win_vt100_enabled:", is_win_vt100_enabled())
   try:
       print("default output:", type(create_output()).__name__)
   except Exception as e:
       print("create_output ERROR:", repr(e))
   PY
   ```
   If `is_win_vt100_enabled` is `False` and/or `create_output()` raises `NoConsoleScreenBufferError`, the bug is confirmed.
3. Hermes already ships a clean ANSI path: `_build_cpr_disabled_output()` builds a `Vt100_Output` with `enable_cpr=False`, but it only triggers over SSH. Confirm `PROMPT_TOOLKIT_NO_CPR=1` forces it:
   ```bash
   PROMPT_TOOLKIT_NO_CPR=1 python -c "from prompt_toolkit.output.vt100 import Vt100_Output, _get_size; from prompt_toolkit.data_structures import Size; Vt100_Output(sys.stdout, lambda: Size(24,80), enable_cpr=False); print('Vt100_Output OK')"
   ```

## The fix
### 1. Force the clean ANSI path (core fix)
Append a TTY-guarded block to the user's `~/.bashrc` (Hermes auto-sources `~/.bashrc` in interactive sessions):
```bash
if [ -t 1 ]; then
    export PROMPT_TOOLKIT_NO_CPR=1
    export COLORTERM=truecolor
    [ -z "$TERM" ] && export TERM=xterm-256color
fi
```
The `[ -t 1 ]` guard keeps this out of piped/non-interactive Hermes runs. A copy-paste block lives in `templates/bashrc_fix.sh`.
VERIFY propagation: re-source bashrc in a real TTY and confirm `PROMPT_TOOLKIT_NO_CPR=1`.

### 2. Tune display config (via `hermes config set` — see Pitfalls)
```bash
hermes config set display.cli_refresh_interval 0   # kill idle background redraws that fight xterm.js auto-scroll
hermes config set display.streaming true            # smooth token-by-token output
hermes config set display.skin <name>               # vivid theme; list in-session with /skin
```
Autocomplete (`SlashCommandCompleter` + `complete_while_typing=True` + `CompletionsMenu(max_height=12)`) is ALREADY wired in `cli.py` (~line 14380 / 15085) — it only looked broken because of the bad renderer. The fix restores it; no code change needed.

### 3. Restart Hermes in the terminal
The already-running session does not have the new env. Re-launch `hermes` inside the Antigravity/VS Code terminal.

## Verification
After restart, run `scripts/probe_rendering.py` under the new env — it should build `Vt100_Output` cleanly with no `NoConsoleScreenBufferError`, and `is_win_vt100_enabled` may still read `False` (that's fine; the env var overrides the path).

## Pitfalls
- `config.yaml` is PROTECTED from direct edit/patch (the patch tool refuses). Use `hermes config set <key> <value>` to write and `hermes config show <key>` to read.
- `TERM_PROGRAM=vscode` is the tell for xterm.js; do NOT be fooled by `TERM=xterm-256color` (the web terminal sets that, unrelated to prompt_toolkit's conhost probe).
- In the shipped prompt_toolkit 3.0.52 build the ONLY relevant env var is `PROMPT_TOOLKIT_NO_CPR`. There is NO `PROMPT_TOOLKIT_FORCE_ANSI`. Force ANSI via the CPR-disabled `Vt100_Output` path, not a non-existent flag.
- Reading `cli.py` (~757KB) with the `read_file` tool can hit `WinError 1455` (paging file too small) on this host. Extract sections with `sed -n 'A,Bp' cli.py` via the terminal tool instead.
- `search_files` can fail with "IO error ... The system cannot find the path specified" for some native Windows paths under git-bash. Use `grep -nE` in the terminal tool for source inspection.

## References
- `references/prompt_toolkit_probe.md` — full reproduction recipe, error transcript, and cli.py anchors.
- `scripts/probe_rendering.py` — re-runnable backend-selection probe.
- `templates/bashrc_fix.sh` — the guarded `~/.bashrc` block to drop in.
