# Drop this at the end of ~/.bashrc. Hermes auto-sources ~/.bashrc in interactive
# sessions, so the vars propagate into the Hermes CLI process.
#
# The [ -t 1 ] guard ensures we ONLY set these for interactive TTYs (the
# Antigravity / VS Code xterm.js terminal). Piped / non-interactive Hermes runs
# are untouched, so output-to-file and automation keep working.
if [ -t 1 ]; then
    export PROMPT_TOOLKIT_NO_CPR=1
    export COLORTERM=truecolor
    [ -z "$TERM" ] && export TERM=xterm-256color
fi
