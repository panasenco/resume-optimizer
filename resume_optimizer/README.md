# Developing resume_optimizer

## Setup

### VS Code Dev Containers / GitHub Codespaces

In VS Code, reopen the project in a devcontainer.
Alternatively, open GitHub Codespaces.
Your project should be automatically installed.

### Just pip

```
pip install -e .[dev]
```

## Formatting and linting

We use [ruff](https://docs.astral.sh/ruff/) for formatting and linting Python code.

### Formatting

```
ruff format resume_optimizer/
```

### linting

List errors:

```
ruff check resume_optimizer/
```

Auto-fix errors:

```
ruff check --fix resume_optimizer/
```