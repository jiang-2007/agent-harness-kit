"""End-to-end offline demo: ReAct turn, streaming, retrieval and parallel fan-out.

Run from the repository root:

    PYTHONPATH=src python3 examples/demo_overview.py

No network or API key is required; the offline providers produce deterministic
replies. The implementation lives in ``harnesskit.demo``.
"""
from harnesskit.demo import main

if __name__ == "__main__":
    main()
