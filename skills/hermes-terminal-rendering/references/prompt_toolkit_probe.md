# prompt_toolkit backend-selection probe (reproduction + anchors)

## Symptom
Hermes CLI flickers, output corrupts on scroll, colors wrong, autocomplete
menu broken — when running in Google Antigravity IDE / VS Code integrated
terminal (xterm.js; `TERM_PROGRAM=vscode`).

## Confirmed reproduction (this host, 2026-07-15)
```
$ echo "$TERM_PROGRAM $TERM $COLORTERM"
vscode xterm-256color truecolor

$ python - <<'PY'
import sys, os
from prompt_toolkit.output.windows10 import is_win_vt100_enabled
from prompt_toolkit.output.defaults import create_output
print("is_win_vt100_enabled:", is_win_vt100_enabled())
try:
    print("default output:", type(create_output()).__name__)
except Exception as e:
    print("create_output ERROR:", repr(e))
PY
is_win_vt100_enabled: False
create_output ERROR: NoConsoleScreenBufferError('Found xterm-256color, while expecting a Windows console...')
```

## Why prompt_toolkit picks the wrong backend
`prompt_toolkit/output/defaults.py::create_output()` on `sys.platform == "win32"`
calls `windows10.is_win_vt100_enabled()`, which opens the REAL console handle via
`windll.kernel32.GetConsoleMode` / `SetConsoleMode(ENABLE_VIRTUAL_TERMINAL_PROCESSING)`
and checks the result. A web-emulated xterm has no real conhost -> returns `False`
-> falls back toward `Win32Output` -> `NoConsoleScreenBufferError`. The renderer
degrades and emits CPR queries (`ESC[6n`) that round-trip badly over the web PTY.

NOTE: prompt_toolkit IGNORES `TERM`/`COLORTERM` for this choice. Setting TERM does
not fix it; only forcing the Vt100/ANSI path via `PROMPT_TOOLKIT_NO_CPR=1` does.

## cli.py anchors (Hermes v0.18.2)
- `from prompt_toolkit.patch_stdout import patch_stdout`  (line 61)
- Hermes' own clean path: `_build_cpr_disabled_output()` -> `Vt100_Output(stdout, _get_term_size, enable_cpr=False)` (lines ~3225-3270). Only invoked when `_terminal_may_leak_cpr()` is true (SSH env or PROMPT_TOOLKIT_NO_CPR=1) — so the env var reuses Hermes' existing correct renderer.
- App construction: `Application(... full_screen=False, refresh_interval=float(...cli_refresh_interval...), erase_when_done=True)` (lines ~15185-15210). `cli_refresh_interval` default 0 disables idle redraws (good — they fight xterm.js auto-scroll).
- Autocomplete is wired: `SlashCommandCompleter` via `ThreadedCompleter` on `TextArea(complete_while_typing=True)` (line ~14380) + `CompletionsMenu(max_height=12, scroll_offset=1)` (line ~15085). Not a bug — just looked broken under the bad renderer.

## Verification after fix
With `PROMPT_TOOLKIT_NO_CPR=1` set, `Vt100_Output(stdout, _sz, enable_cpr=False)`
builds cleanly. `is_win_vt100_enabled` may still be `False` — that's fine; the env
var selects the ANSI path. Restart Hermes in the terminal to pick up the new env.
