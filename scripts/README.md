This folder contains utility scripts for development and local testing.

Guidelines:
- Use scripts/* for small developer utilities (GPU checks, quick environment checks).
- For longer demos and ad-hoc tests, see tests/legacy/ where historical demo/test scripts were moved.

Common commands (PowerShell):

Activate the venv:

    .venv\Scripts\Activate.ps1

Run the GPU check script:

    python scripts\check_gpu_init.py

Note: scripts import from `src/` so ensure the current working directory is the repository root when running.
