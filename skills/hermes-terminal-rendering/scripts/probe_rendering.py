#!/usr/bin/env python
"""Re-runnable probe: which prompt_toolkit output backend will Hermes use here?

Run from the Hermes venv:
    venv/Scripts/python.exe scripts/probe_rendering.py

Exit 0  = clean ANSI/Vt100 path selected (good for xterm.js web terminals)
Exit 1  = backend probe failed / NoConsoleScreenBufferError (the flicker bug)
"""
import os
import sys

try:
    from prompt_toolkit.output.windows10 import is_win_vt100_enabled
    from prompt_toolkit.output.defaults import create_output
    from prompt_toolkit.output.vt100 import Vt100_Output, _get_size
    from prompt_toolkit.data_structures import Size
except Exception as e:  # pragma: no cover
    print("FATAL: cannot import prompt_toolkit:", repr(e))
    sys.exit(2)

print("sys.platform         :", sys.platform)
print("TERM                 :", os.environ.get("TERM"))
print("COLORTERM            :", os.environ.get("COLORTERM"))
print("TERM_PROGRAM         :", os.environ.get("TERM_PROGRAM"))
print("PROMPT_TOOLKIT_NO_CPR:", repr(os.environ.get("PROMPT_TOOLKIT_NO_CPR")))
print("is_win_vt100_enabled :", is_win_vt100_enabled())

# What backend does the default path pick?
try:
    out = create_output()
    print("default output class :", type(out).__name__)
except Exception as e:
    print("default output ERROR :", repr(e))
    print("=> Backend probe FAILED. This is the flicker/scroll-corruption bug.")
    print("   Fix: export PROMPT_TOOLKIT_NO_CPR=1 (forces Vt100_Output, CPR off).")
    sys.exit(1)

# Confirm the NO_CPR ANSI path builds cleanly (the target state).
try:
    def _sz():
        try:
            r, c = _get_size(sys.stdout.fileno())
            return Size(rows=r or 24, columns=c or 80)
        except Exception:
            return Size(rows=24, columns=80)
    Vt100_Output(sys.stdout, _sz, enable_cpr=False)
    print("Vt100/ANSI(CPR off)  : builds OK (clean path for xterm.js)")
except Exception as e:
    print("Vt100 path ERROR     :", repr(e))

sys.exit(0)
