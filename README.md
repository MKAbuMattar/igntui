<div align="center">

# igntui

<div align="center">
  <a href="https://github.com/MKAbuMattar/igntui" target="_blank" rel="noreferrer">
    <img src="https://img.shields.io/badge/github-%23181717.svg?style=for-the-badge&logo=github&logoColor=white" alt="GitHub Repository"/>
  </a>

  <a href="https://github.com/MKAbuMattar/igntui/releases" target="_blank" rel="noreferrer">
    <img alt="GitHub Release" src="https://img.shields.io/github/v/release/MKAbuMattar/igntui?color=%232563eb&label=Latest%20Release&style=for-the-badge&logo=github" />
  </a>

  <a href="https://pypi.org/project/igntui/" target="_blank" rel="noreferrer">
    <img src="https://img.shields.io/pypi/v/igntui?style=for-the-badge&logo=pypi&logoColor=white&color=2563eb&label=PyPI" alt="PyPI Version"/>
  </a>

  <a href="https://pypi.org/project/igntui/" target="_blank" rel="noreferrer">
    <img src="https://img.shields.io/pypi/pyversions/igntui?style=for-the-badge&logo=python&logoColor=white&color=2563eb&label=Python" alt="Python Versions"/>
  </a>

  <a href="/LICENSE" target="_blank" rel="noreferrer">
    <img alt="GPL-3.0 License" src="https://img.shields.io/github/license/MKAbuMattar/igntui?color=%232563eb&style=for-the-badge&label=License">
  </a>

  <a href="https://github.com/MKAbuMattar/igntui/stargazers" target="_blank" rel="noreferrer">
    <img alt="GitHub Stars" src="https://img.shields.io/github/stars/MKAbuMattar/igntui?color=%232563eb&label=Stars&style=for-the-badge&logo=github">
  </a>

  <a href="https://pypi.org/project/igntui/" target="_blank" rel="noreferrer">
    <img alt="PyPI Downloads" src="https://img.shields.io/pypi/dm/igntui?color=%232563eb&style=for-the-badge&logo=pypi&label=Downloads">
  </a>

  <a href="https://github.com/MKAbuMattar/igntui/issues" target="_blank" rel="noreferrer">
    <img alt="GitHub Issues" src="https://img.shields.io/github/issues/MKAbuMattar/igntui?color=%232563eb&style=for-the-badge&logo=github&label=Issues">
  </a>
</div>

<br/>

[🌐 Website](https://mkabumattar.com/) • [📦 PyPI](https://pypi.org/project/igntui/) • [🚀 Quick Start](#-installation) • [💬 Support](https://github.com/MKAbuMattar/igntui/issues)

<br/>

---

> A powerful Terminal User Interface (TUI) and CLI for generating `.gitignore` files from [gitignore.io](https://www.toptal.com/developers/gitignore) templates.

</div>

## ✨ Features

### 🎨 Interactive TUI Mode

- **Smart Search** - Fuzzy, exact, and regex search modes (F1/F2/F3)
- **Multi-Template Selection** - Select and combine multiple templates
- **Live Preview** - See generated `.gitignore` content in real-time
- **Intuitive Navigation** - Tab between panels, arrow keys, vim-style shortcuts
- **Beautiful Interface** - Animated splash screen with pyfiglet ASCII art

### ⚡ Performance

- **Intelligent Caching** - Local template caching for instant access
- **Async Loading** - Non-blocking template loading and generation
- **Rate Limiting** - Respects API limits automatically

### 💾 Export & Save

- **Save to File** - Save generated `.gitignore` with custom paths
- **Export Templates** - Export selected templates as JSON
- **Overwrite Protection** - Confirmation dialogs for existing files

### 🛠️ CLI Mode

- **Quick Generation** - Generate `.gitignore` from command line
- **List Templates** - Browse 571+ available templates
- **Test Connection** - Verify API connectivity
- **Cache Management** - Clear and manage local cache

## 📦 Installation

### Using pip (Standard)

```bash
pip install igntui
```

### Using pipx (Isolated)

[pipx](https://pipx.pypa.io/) installs the package in an isolated environment:

```bash
pipx install igntui
```

### From source

```bash
git clone https://github.com/MKAbuMattar/igntui.git
cd igntui
pip install -e .
```

### Windows Requirements

On Windows, you'll need the `windows-curses` package:

```bash
pip install windows-curses
```

## 🚀 Quick Start

### Launch TUI (Interactive Mode)

```bash
igntui
```

or

```bash
python -m igntui
```

### CLI Commands

#### Generate `.gitignore`

```bash
# Single template
igntui generate python

# Multiple templates
igntui generate python node visualstudiocode

# Save to file (also writes .igntui.cfg.toml sidecar by default)
igntui generate python --output .gitignore

# Preview without writing
igntui generate python --output .gitignore --dry-run

# Skip writing the sidecar
igntui generate python --output .gitignore --no-sidecar

# Overwrite without prompt
igntui generate python --output .gitignore --force
```

#### List Available Templates

```bash
# List all templates
igntui list

# Filter by pattern
igntui list --filter python

# Show count only
igntui list --count
```

#### Test API Connection

```bash
igntui test
igntui test --timeout 5
```

#### Cache Management

```bash
igntui cache info             # show cache stats
igntui cache stats            # show usage statistics
igntui cache clear --force    # clear all cached entries
```

#### Global Flags

```bash
igntui --no-cache list                  # bypass cache for the session
igntui --config /path/to/config.json    # load alternate config
igntui --verbose <command>              # verbose / debug output
igntui --version                        # print version + Python + OS
```

#### Project Sidecar (`.igntui.cfg.toml`)

When you save a `.gitignore` (via TUI or CLI), igntui writes a small TOML
sidecar next to it that pins the templates and search mode used. Re-running
`igntui` in the same directory **auto-loads** that selection so you can iterate
without re-picking templates. The sidecar is safe to commit so teammates
inherit the same starting state.

```toml
# .igntui.cfg.toml
schema_version = 1
generated_at   = "2026-04-27T12:00:00Z"
igntui_version = "0.0.2"

[selection]
templates   = ["python", "node", "macos"]
search_mode = "fuzzy"

[output]
path                = ".gitignore"
preserve_user_edits = true
```

User-added rules outside the `# >>> igntui >>>` / `# <<< igntui <<<` markers
are preserved on every re-save.

#### Shell Completion

```bash
# bash
eval "$(igntui completion bash)"

# zsh — install to a directory on $fpath
igntui completion zsh > ~/.zsh/completions/_igntui

# fish
igntui completion fish | source
```

## 🎮 TUI Usage

### Keyboard Shortcuts

#### Navigation

- `Tab` / `Shift+Tab` — Navigate between panels
- `↑` / `↓` — Move selection up/down
- `PgUp` / `PgDn` — Page up/down
- `Home` / `End` — Jump to top/bottom
- `/` — Focus the Search panel
- `Esc` (in Search) — Exit search mode and return to Templates

#### Search Modes

- `F1` — Fuzzy search (default)
- `F2` — Exact search
- `F3` — Regex search

#### Template Management

- `Space` / `Enter` — Select/deselect template
- `a` — Select all visible (filtered) templates
- `x` — Remove all visible templates from selection
- `c` — Clear entire selection

#### Actions

- `s` — Save `.gitignore` (writes `.igntui.cfg.toml` sidecar; shows diff preview if file exists)
- `e` — Export selected templates as JSON
- `r` / `F5` — Refresh template list from API
- `h` / `?` / `F12` — Show help dialog
- `i` — Show app info
- `q` / `Esc` (outside Search) — Quit application

#### Mouse Support

- **Click** a panel to focus it
- **Click** a row in Templates to select it (and toggle on the same click)
- **Scroll wheel** scrolls the panel under the cursor without changing focus

### Panel Layout

```
┌─────────────────────────────┬──────────────────────────────────┐
│  Search Panel               │  Generated Content Panel         │
│  (Filter templates)         │  (Preview .gitignore)            │
├─────────────────────────────┤                                  │
│  Available Templates        │                                  │
│  (571+ templates)           │                                  │
│                             │                                  │
│  • Select with Space        │                                  │
│  • Multi-select support     │                                  │
│  • Smart search             │                                  │
├─────────────────────────────┴──────────────────────────────────┤
│  Selected Templates (Bottom Panel)                             │
│  • Shows your current selection                                │
│  • Remove with Space                                           │
└────────────────────────────────────────────────────────────────┘
│  Status Bar                                                    │
│  • Keyboard shortcuts • Current mode • Status messages         │
└────────────────────────────────────────────────────────────────┘
```

## 🎯 Use Cases

### For Developers

```bash
# Python project
igntui generate python venv

# Node.js project
igntui generate node npm yarn

# Full-stack project
igntui generate python node react visualstudiocode

# Unity game development
igntui generate unity visualstudio windows
```

### For Teams

```bash
# Export team's template selection
igntui  # Select templates in TUI, press 'e' to export

# Share the JSON file with team
# Others can import and use the same templates
```

## ⚙️ Configuration

Configuration file location: `~/.igntui.cfg.toml`

### Default Configuration

```json
{
  "api": {
    "base_url": "https://www.toptal.com/developers/gitignore/api",
    "timeout": 10,
    "cache_ttl": 3600,
    "retry_attempts": 3
  },
  "ui": {
    "theme": "default",
    "mouse_support": true,
    "animation_speed": 150
  },
  "behavior": {
    "fuzzy_search_threshold": 0.6,
    "max_recent_templates": 10
  }
}
```

## 🐛 Troubleshooting

### Windows: "igntui is not recognized"

If you see `'igntui' is not recognized as an internal or external command`, the Scripts directory is not in your PATH.

**Quick Fix - Use Python Module:**

```powershell
python -m igntui
```

**Permanent Fix - Add to PATH:**

1. Press `Win + X` and select "System"
2. Click "Advanced system settings" → "Environment Variables"
3. Under "User variables", select "Path" and click "Edit"
4. Click "New" and add: `C:\Users\YOUR_USERNAME\AppData\Roaming\Python\Python3XX\Scripts`
5. Click "OK" and **restart your terminal**

Or use PowerShell (as Administrator):

```powershell
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
$newPath = $currentPath + ";C:\Users\$env:USERNAME\AppData\Roaming\Python\Python313\Scripts"
[Environment]::SetEnvironmentVariable("Path", $newPath, "User")
```

### Linux/macOS: Permission Denied

If you get permission errors:

```bash
# Use --user flag
pip install --user igntui

# Or add ~/.local/bin to PATH
export PATH="$HOME/.local/bin:$PATH"
```

### ImportError: No module named 'curses'

On Windows, install windows-curses:

```bash
pip install windows-curses
```

### API Connection Issues

If templates won't load:

1. Check internet connection
2. Test API: `igntui test`
3. Clear cache: `igntui cache --clear`
4. Try with verbose: `igntui --verbose`

## 🧪 Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/MKAbuMattar/igntui.git
cd igntui

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/igntui
isort src/igntui

# Type checking
mypy src/igntui
```

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=igntui

# Specific test file
pytest tests/test_api.py
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Mohammad Abu Mattar**

- GitHub: [@MKAbuMattar](https://github.com/MKAbuMattar)
- Website: [MKAbuMattar.com](https://mkabumattar.com)
- Email: info@mkabumattar.com

## 🙏 Acknowledgments

- [gitignore.io](https://www.toptal.com/developers/gitignore) - Template source
- [pyfiglet](https://github.com/pwaller/pyfiglet) - ASCII art generation
- [Python curses](https://docs.python.org/3/library/curses.html) - Terminal UI framework

## 📊 Statistics

- **571+ Templates** - Comprehensive template library
- **Smart Caching** - Reduces API calls by 90%
- **3 Search Modes** - Fuzzy, exact, and regex
- **Multi-select** - Combine unlimited templates
- **Cross-platform** - Windows, macOS, Linux

## 🔗 Links

- **Repository**: https://github.com/MKAbuMattar/igntui
- **Issue Tracker**: https://github.com/MKAbuMattar/igntui/issues
- **PyPI Package**: https://pypi.org/project/igntui/
- **Documentation**: https://github.com/MKAbuMattar/igntui/wiki (coming soon)

---

<div align="center">
  <strong>Made with ❤️ by Mohammad Abu Mattar</strong>
  <br>
  <sub>Give it a ⭐ if you like it!</sub>
</div>
