# Devin DCC

A CLI app to aid tools development for DCC software.

## Caveats

This project mainly exists so I don't have to re-write the scripts to set up and run DCCs every time I create a new DCC tool project.

No other use-cases are currently considered and, there's no guarantees regarding stability of the CLI, package or even project name and visibility.

The project is public mainly as an example for anyone who wants to do something similar and for my portfolio.

## Usage

Install with [uv](https://docs.astral.sh/uv/) or pipx:

```shell
uv tool install devin-dcc --from https://github.com/henrikwilhelmsen/devin-dcc.git
```

Show available commands:

```shell
devin --help
```

Or run without installing:

```shell
uvx --from https://github.com/henrikwilhelmsen/devin-dcc.git devin --help
```

Launch MotionBuilder 2025 with extra dependencies:

```shell
uvx --from https://github.com/henrikwilhelmsen/devin-dcc.git --python 3.11 --with <dependency> devin mobu -v 2025 --include-prefix-site
```

## Development

Requires [uv package manager](https://docs.astral.sh/uv/)

Clone the project with Git:

```shell
git clone https://github.com/henrikwilhelmsen/devin-dcc.git
```

Create venv and sync dependencies:

```shell
uv sync --dev
```

### Testing

Run pytest:

```shell
uv run pytest -v
```

Test the CLI while developing:

```shell
uv run devin <command>
```

For the Maya tests that require a specific version, the MAYA_VERSION environment variable needs to be set to a valid installed version, otherwise the tests will be skipped.

### Building a distribution with PyInstaller

Build a portable single file executable:

```shell
uv run pyinstaller .\src\devin\__init__.py --name devin --add-data .\src\devin\data:data --onefile
```
