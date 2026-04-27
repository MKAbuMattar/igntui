#!/usr/bin/env python3
"""`igntui completion <shell>` — emit a shell completion script."""

import argparse

from ..base import CLICommand

_SUBCOMMANDS = ["tui", "list", "generate", "cache", "test", "completion"]
_GLOBAL_FLAGS = "--version --verbose --log-level --config --no-cache --help"


_BASH = """\
# bash completion for igntui — install with:
#   eval "$(igntui completion bash)"
# or save to /etc/bash_completion.d/igntui
_igntui_complete() {
    local cur prev words cword
    _init_completion || return

    local subcommands="%(subcommands)s"
    local global_flags="%(global_flags)s"

    # First positional after `igntui` (skipping global flags) is the subcommand.
    local cmd=""
    local i
    for ((i = 1; i < cword; i++)); do
        case "${words[i]}" in
            -*) continue ;;
            *) cmd="${words[i]}"; break ;;
        esac
    done

    case "$cmd" in
        tui)       COMPREPLY=( $(compgen -W "--no-splash" -- "$cur") ); return ;;
        list)      COMPREPLY=( $(compgen -W "--filter --count" -- "$cur") ); return ;;
        generate)  COMPREPLY=( $(compgen -W "--output --append --force --dry-run --no-sidecar" -- "$cur") ); return ;;
        cache)     COMPREPLY=( $(compgen -W "info stats clear --force" -- "$cur") ); return ;;
        test)      COMPREPLY=( $(compgen -W "--timeout" -- "$cur") ); return ;;
        completion) COMPREPLY=( $(compgen -W "bash zsh fish" -- "$cur") ); return ;;
        "")        COMPREPLY=( $(compgen -W "$subcommands $global_flags" -- "$cur") ); return ;;
    esac
}
complete -F _igntui_complete igntui
complete -F _igntui_complete gitignore-tui
"""


_ZSH = """\
#compdef igntui gitignore-tui
# zsh completion for igntui — install with:
#   eval "$(igntui completion zsh)"
# or save to a directory on $fpath as _igntui

_igntui() {
    local -a subcommands global_flags
    subcommands=(%(subcommands_quoted)s)
    global_flags=(--version --verbose --log-level --config --no-cache --help)

    local context state line
    _arguments -C \\
        '1:command:->cmd' \\
        '*::arg:->args'

    case $state in
        cmd) _describe 'command' subcommands ;;
        args)
            case $line[1] in
                tui)       _arguments '--no-splash[skip splash screen]' ;;
                list)      _arguments '--filter[pattern]:pattern:' '--count[show count only]' ;;
                generate)  _arguments \\
                    '--output[output file]:file:_files' \\
                    '--append[append to existing]' \\
                    '--force[overwrite without prompt]' \\
                    '--dry-run[print without writing]' \\
                    '--no-sidecar[skip igntui.cfg.toml]' ;;
                cache)     _values 'cache action' info stats clear ;;
                test)      _arguments '--timeout[seconds]:seconds:' ;;
                completion) _values 'shell' bash zsh fish ;;
            esac
            ;;
    esac
}

_igntui "$@"
"""


_FISH = """\
# fish completion for igntui — install with:
#   igntui completion fish | source
# or save to ~/.config/fish/completions/igntui.fish

complete -c igntui -f
complete -c gitignore-tui -f

set -l __igntui_subs %(subcommands_space)s

complete -c igntui -n "not __fish_seen_subcommand_from $__igntui_subs" -a "$__igntui_subs"
complete -c igntui -l version -d "Show version"
complete -c igntui -l verbose -d "Verbose output"
complete -c igntui -l no-cache -d "Disable caching"
complete -c igntui -l config -d "Custom config file" -r

complete -c igntui -n "__fish_seen_subcommand_from tui" -l no-splash -d "Skip splash"
complete -c igntui -n "__fish_seen_subcommand_from list" -l filter -d "Filter pattern" -r
complete -c igntui -n "__fish_seen_subcommand_from list" -l count -d "Show count only"
complete -c igntui -n "__fish_seen_subcommand_from generate" -l output -d "Output file" -r
complete -c igntui -n "__fish_seen_subcommand_from generate" -l dry-run -d "Print without writing"
complete -c igntui -n "__fish_seen_subcommand_from generate" -l no-sidecar -d "Skip sidecar"
complete -c igntui -n "__fish_seen_subcommand_from generate" -l force -d "Overwrite without prompt"
complete -c igntui -n "__fish_seen_subcommand_from cache" -a "info stats clear"
complete -c igntui -n "__fish_seen_subcommand_from completion" -a "bash zsh fish"
"""


_TEMPLATES = {"bash": _BASH, "zsh": _ZSH, "fish": _FISH}


class CompletionCommand(CLICommand):
    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "shell",
            choices=["bash", "zsh", "fish"],
            help="Shell to emit completion script for",
        )

    def execute(self, args: argparse.Namespace) -> int:
        template = _TEMPLATES[args.shell]
        print(
            template
            % {
                "subcommands": " ".join(_SUBCOMMANDS),
                "subcommands_quoted": " ".join(f'"{s}"' for s in _SUBCOMMANDS),
                "subcommands_space": " ".join(_SUBCOMMANDS),
                "global_flags": _GLOBAL_FLAGS,
            }
        )
        return 0
