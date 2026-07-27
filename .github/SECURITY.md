# Security Policy

## Supported versions

Fixes land on the latest release published to [PyPI](https://pypi.org/project/igntui/). There
are no maintained release branches — please upgrade before reporting.

```bash
pipx upgrade igntui    # or: pip install --upgrade igntui
```

## Reporting

Report privately through
[GitHub Security Advisories](https://github.com/MKAbuMattar/igntui/security/advisories/new).
Please don't open a public issue for a suspected vulnerability.

Expect an acknowledgement within a few days. Because this is maintained in spare time, a fix
may take longer — you'll be told where it stands.

## Realistic scope

igntui fetches text over HTTPS, caches it, and writes files into your project. The parts that
could matter:

- **The write path.** `igntui generate --output` and the TUI's save flow write to a path you
  give them, and re-save splices into an existing file. Anything that could make igntui write
  outside the intended path, clobber content outside the managed block, or destroy the custom
  patterns region is in scope.
- **Template names reaching the API and the filesystem.** `GitIgnoreAPI._clean_technology_names`
  strips names to `alnum` plus `-_+.` and rejects `..`, `//`, `\\`, `<`, `>`, `|`. Cache keys
  are sha256 prefixes rather than names for the same reason. A bypass that gets a crafted name
  into a URL or a filename is in scope.
- **The cache directory.** `~/.cache/igntui` holds API responses as JSON. Anything that makes
  igntui read or write outside it, or trust a file in it that it should not, is in scope.
- **Config and sidecar parsing.** `~/.igntui.cfg.toml`, `.igntui.repo.cfg.toml`, the per-output
  sidecar, and `~/.igntui.usage.toml` are all parsed with `tomllib`. The repo config is
  team-shared, so it is the one an attacker is most likely to influence — it can set `api.base_url`,
  which redirects where templates are fetched from.
- **Terminal escape sequence injection.** Template content comes from a remote API and is
  rendered in a curses pane and written to disk. A response that can emit attacker-controlled
  control bytes to the terminal is in scope.
- **The release pipeline.** A compromised published artifact is the highest-impact scenario
  here, well above anything in the application itself.

## Out of scope

- Garbled rendering in a terminal below the size the panels can lay out. That is a bug — please
  file it as a TUI problem.
- The animation or splash screen leaving the terminal in an odd state after an abnormal exit.
  Also a bug, also a regular issue.
- Reachability of `gitignore.io` itself, or its content.
- Automated scanner output with no demonstrated impact on this package.
