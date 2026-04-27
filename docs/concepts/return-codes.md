# Exit Codes

Process exit codes for every `igntui` command.

## SUMMARY

| Code | Meaning                                                   |
| ---- | --------------------------------------------------------- |
| `0`  | Success                                                   |
| `1`  | General failure (network, filesystem, validation, cancel) |
| `2`  | Argument parse error (from argparse)                      |

## PER-COMMAND

### `igntui` (no subcommand)

Exits with the code of the implicit `tui` invocation.

### `igntui tui`

| Code | Cause                                                      |
| ---- | ---------------------------------------------------------- |
| `0`  | TUI exited normally (user quit with `q` or `Esc`)          |
| `1`  | curses unavailable, terminal incompatible, fatal exception |

### `igntui list`

| Code | Cause                                             |
| ---- | ------------------------------------------------- |
| `0`  | Templates listed                                  |
| `1`  | API failure, or `--filter` matched zero templates |

### `igntui generate`

| Code | Cause                                                                |
| ---- | -------------------------------------------------------------------- |
| `0`  | Content written or printed                                           |
| `1`  | API failure, empty content, file write error, user said no at prompt |

### `igntui cache info` / `cache stats`

| Code | Cause                        |
| ---- | ---------------------------- |
| `0`  | Information printed          |
| `1`  | Cache directory inaccessible |

### `igntui cache clear`

| Code | Cause                                                   |
| ---- | ------------------------------------------------------- |
| `0`  | Cache cleared (or user declined the prompt)             |
| `1`  | User cancelled at the prompt, or filesystem write error |

### `igntui test`

| Code | Cause                               |
| ---- | ----------------------------------- |
| `0`  | API responded with success          |
| `1`  | Network failure or non-2xx response |

### `igntui completion`

| Code | Cause                                         |
| ---- | --------------------------------------------- |
| `0`  | Completion script printed                     |
| `2`  | Unknown shell argument (rejected by argparse) |

## DEBUGGING NON-ZERO EXITS

Re-run with `--verbose` to get a Python traceback on stderr:

```
$ igntui --verbose generate something-weird --output /etc/.gitignore
```

For systemic problems, check the log file at `~/.igntui.log` (rotating;
configured under [`logging`](../files/user-config.md#logging)).

## SEE ALSO

- [`igntui --verbose`](../reference/igntui.md#--verbose)
- [User configuration: logging](../files/user-config.md#logging)
