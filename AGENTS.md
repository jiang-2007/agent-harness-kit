# AGENTS

Guidance for automated agents and contributors working in this repository.

- Runtime core lives under `src/harnesskit/`; tests under `tests/`.
- Keep the standard-library core dependency-free. Optional backends belong
  behind the `LLMProvider` interface.
- Every new tool must subclass `Tool`, declare its `parameters`, and ship a
  unit test in `tests/`.
- Run `PYTHONPATH=src python3 -m unittest discover -s tests` before opening a
  pull request.
- Do not hardcode API keys, tokens or local paths in source.
