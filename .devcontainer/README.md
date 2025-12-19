# Development Container

This devcontainer provides a complete development environment for the Compit Home Assistant integration.

## Features

- **Python 3.12** on Debian Bookworm
- **Home Assistant** development environment
- **Pre-configured VS Code extensions**:
  - Python with Pylance
  - Ruff linter and formatter
  - Black formatter
  - YAML and JSON support
  - GitHub integration

## Getting Started

1. Open this project in VS Code
2. Click "Reopen in Container" when prompted (or use Command Palette: `Dev Containers: Reopen in Container`)
3. Wait for the container to build and setup to complete
4. Start developing!

## Running Home Assistant

To run Home Assistant with your integration:

```bash
scripts/develop
```

Home Assistant will be available at http://localhost:8123

## Linting and Formatting

```bash
# Run all linters
scripts/lint

# Auto-fix with Ruff
ruff check --fix custom_components/compit

# Format with Black
black custom_components/compit
```

## Pre-commit Hooks

Install pre-commit hooks to automatically lint and format on commit:

```bash
pip install pre-commit
pre-commit install
```

## Environment

- Python: 3.12
- Home Assistant: 2024.12.0
- Linter: Ruff 0.8.4
- Formatter: Black 24.10.0
