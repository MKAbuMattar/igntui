# ~/.igntui.cfg.toml

## NAME

`~/.igntui.cfg.toml` — user-level configuration

## LOCATION

`~/.igntui.cfg.toml` by default. Override with the global
[`--config <path>`](../reference/igntui.md#--config-path--c) flag.

## SYNOPSIS

```json
{
  "api": {
    "base_url": "https://www.toptal.com/developers/gitignore/api",
    "timeout": 10,
    "user_agent": "igntui/0.0.2",
    "cache_ttl": 3600,
    "retry_attempts": 3
  },
  "ui": {
    "theme": "default",
    "mouse_support": true,
    "auto_save": false,
    "panel_layout": "four_panel",
    "show_help": true,
    "animation_speed": 150
  },
  "behavior": {
    "max_recent_templates": 10,
    "auto_refresh_interval": 3600,
    "fuzzy_search_threshold": 0.6,
    "save_usage_stats": true,
    "auto_backup": true,
    "max_cache_entries": 1000
  },
  "logging": {
    "level": "INFO",
    "file_enabled": true,
    "console_enabled": false,
    "max_file_size": 10485760,
    "backup_count": 5
  }
}
```

## DESCRIPTION

The user config is loaded at startup and merged on top of `DEFAULT_CONFIG`
defined in `core/config.py`. Missing keys fall back to defaults; unknown
keys are preserved (ignored at read time, written back on save). The merge
is deep — nested objects are merged recursively, not replaced.

After the file is read, environment variables (see
[Environment variables](../reference/igntui.md#environment-variables))
override matching keys.

## SECTIONS

### `api`

| Key              | Type    | Default                                             | Notes                                          |
| ---------------- | ------- | --------------------------------------------------- | ---------------------------------------------- |
| `base_url`       | string  | `"https://www.toptal.com/developers/gitignore/api"` | gitignore.io endpoint                          |
| `timeout`        | integer | `10`                                                | HTTP request timeout in seconds                |
| `user_agent`     | string  | `"igntui/<version>"`                                | sent in `User-Agent` header                    |
| `cache_ttl`      | integer | `3600`                                              | seconds; see [Caching](../concepts/caching.md) |
| `retry_attempts` | integer | `3`                                                 | per-request retry budget                       |

### `ui`

| Key               | Type    | Default        | Notes                                   |
| ----------------- | ------- | -------------- | --------------------------------------- |
| `theme`           | string  | `"default"`    | currently only `default` is implemented |
| `mouse_support`   | boolean | `true`         | enables click-to-focus and scroll-wheel |
| `auto_save`       | boolean | `false`        | reserved (not yet honored)              |
| `panel_layout`    | string  | `"four_panel"` | reserved                                |
| `show_help`       | boolean | `true`         | reserved                                |
| `animation_speed` | integer | `150`          | reserved                                |

### `behavior`

| Key                      | Type    | Default | Notes                                              |
| ------------------------ | ------- | ------- | -------------------------------------------------- |
| `max_recent_templates`   | integer | `10`    | how many recents pin to the top of Templates panel |
| `auto_refresh_interval`  | integer | `3600`  | seconds; reserved                                  |
| `fuzzy_search_threshold` | float   | `0.6`   | reserved                                           |
| `save_usage_stats`       | boolean | `true`  | enables `~/.igntui.usage.toml`                     |
| `auto_backup`            | boolean | `true`  | reserved                                           |
| `max_cache_entries`      | integer | `1000`  | reserved (no eviction policy yet enforces it)      |

### `logging`

| Key               | Type    | Default    | Notes                                    |
| ----------------- | ------- | ---------- | ---------------------------------------- |
| `level`           | string  | `"INFO"`   | one of DEBUG/INFO/WARNING/ERROR/CRITICAL |
| `file_enabled`    | boolean | `true`     | write to `~/.igntui.log`                 |
| `console_enabled` | boolean | `false`    | also write to stderr                     |
| `max_file_size`   | integer | `10485760` | rotate at 10 MiB                         |
| `backup_count`    | integer | `5`        | number of rotated files to keep          |

## RELATED FILES

| Path                   | Purpose                                                           |
| ---------------------- | ----------------------------------------------------------------- |
| `~/.cache/igntui/`     | cache directory (TTL controlled by `api.cache_ttl`)               |
| `~/.igntui.log`        | rotating log file                                                 |
| `~/.igntui.usage.toml` | recently-used templates (see [Usage data](usage-data.md))         |
| `./igntui.cfg.toml`    | per-project sidecar (see [`.igntui.cfg.toml`](igntui-cfg-toml.md)) |

## EXAMPLES

### Override the API endpoint for a private mirror

```json
{
  "api": {
    "base_url": "https://gitignore.internal.example.com/api",
    "user_agent": "igntui/0.0.2 (internal)"
  }
}
```

### Disable mouse support on a non-mouse-friendly terminal

```json
{
  "ui": {
    "mouse_support": false
  }
}
```

### Verbose file logging

```json
{
  "logging": {
    "level": "DEBUG",
    "file_enabled": true,
    "max_file_size": 52428800,
    "backup_count": 10
  }
}
```

## SEE ALSO

- [`igntui` global flags](../reference/igntui.md)
- [`.igntui.cfg.toml`](igntui-cfg-toml.md)
- [Caching](../concepts/caching.md)
