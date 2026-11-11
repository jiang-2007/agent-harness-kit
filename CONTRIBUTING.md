# Contributing

Thanks for considering a contribution! This project is study-grade and keeps
the core dependency-free, so changes should stay small, explicit and tested.

## Development setup

```bash
git clone https://github.com/jiang-2007/agent-harness-kit.git
cd agent-harness-kit
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e .
```

## Running tests

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

## What to work on

- New built-in tools following the `Tool` base class.
- A real provider backend (OpenAI-compatible gateway, local model).
- Memory strategies beyond the sliding window.
- Additional policy checks (spend cap, read-only mode, dry run).
- Documentation, examples and tests.

## Pull request checklist

- [ ] Tests pass locally (`unittest discover`).
- [ ] Public functions and classes have a short docstring.
- [ ] No third-party runtime dependency added without a discussion first.
- [ ] `CHANGELOG.md` entry added under `Unreleased`.

## Commit style

Use short imperative messages, e.g. `add calculator tool`, `document agent yaml spec`.
