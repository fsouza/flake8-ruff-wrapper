# flake8-ruff-wrapper

This is a package that allows you to use
[ruff](https://github.com/charliermarsh/ruff) as a replacement to
[flake8](https://github.com/PyCQA/flake8) without migrating your configuration to pyproject.toml and keeping the config format

It actually depends on flake8 and ruff and simply bridges the two tools.

Usage:

```
% cat .flake8
[flake8]
ignore = E203,W503
max-line-length = 88
% flake8-ruff some_file.py
# invokes ruff with configuration that matches the settings defined in .flake8
```

## Using with pre-commit

See [pre-commit](https://github.com/pre-commit/pre-commit) for instructions

Sample `.pre-commit-config.yaml`

```yaml
-   repo: https://github.com/fsouza/flake8-ruff-wrapper
    rev: v0.2.0
    hooks:
    -   id: flake8-ruff
```
