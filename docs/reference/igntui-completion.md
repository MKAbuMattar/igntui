# igntui completion

## NAME

`igntui completion` — emit a shell completion script

## SYNOPSIS

```
igntui [global-options] completion {bash | zsh | fish}
```

## DESCRIPTION

Prints a static shell-completion script for the requested shell to stdout.
The script completes:

- Top-level subcommands (`tui`, `list`, `generate`, `cache`, `test`,
  `completion`)
- Flags per subcommand
- The `bash`/`zsh`/`fish` choice for `igntui completion`
- The `info`/`stats`/`clear` actions for `igntui cache`

Both `igntui` and `gitignore-tui` are wired up.

The script does **not** complete template names dynamically — that would
require a live API call on every Tab. Use the TUI for template discovery.

## OPTIONS

### `<shell>`

(positional, required, one of) `bash`, `zsh`, or `fish`. The shell to emit
completion for.

## EXAMPLES

### Bash — eval at shell startup

Add to `~/.bashrc`:

```bash
eval "$(igntui completion bash)"
```

Or install system-wide:

```bash
sudo igntui completion bash > /etc/bash_completion.d/igntui
```

### Zsh — install to `$fpath`

```bash
mkdir -p ~/.zsh/completions
igntui completion zsh > ~/.zsh/completions/_igntui
```

Then ensure `~/.zsh/completions` is on `$fpath` in `~/.zshrc`:

```bash
fpath=(~/.zsh/completions $fpath)
autoload -U compinit && compinit
```

### Fish — drop into completions

```fish
igntui completion fish > ~/.config/fish/completions/igntui.fish
```

Or for the current shell only:

```fish
igntui completion fish | source
```

## OUTPUT

A complete shell script for the requested shell, ready to be sourced or
saved. No additional output.

## EXIT CODES

| Code | Meaning                            |
| ---- | ---------------------------------- |
| `0`  | Success                            |
| `2`  | Unknown shell (argparse rejection) |

## SEE ALSO

- [`igntui`](igntui.md) — global flags that the completions cover
