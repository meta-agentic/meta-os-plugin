# .githooks.d/ — this instance's own git hooks

The hooks in `.githooks/` are stubs. Each hands over to the meta-os plugin's check, then runs every executable file in `.githooks.d/<hook>/` whose name is letters, digits, `_` and `-` only (so `*.orig`, `*~` and editor swap files never run), in name order, with the hook's arguments. The first that fails fails the hook.

    .githooks.d/pre-commit/10-my-gate      # chmod +x; runs after the plugin's check
    .githooks.d/commit-msg/10-my-check     # gets the message file as $1

Handled today: `pre-commit`, `commit-msg`. Hooks run only in a clone that enabled them: `git config core.hooksPath .githooks`.

When the plugin is not installed on a machine, the stub warns, still runs the hooks here, and lets the commit through. Set `hooks.strict` to `true` in `meta-os.config.json` to refuse instead, for every clone of this instance. `META_OS_HOOK_STRICT=1` makes one machine strict; nothing makes one machine weaker than the instance.
