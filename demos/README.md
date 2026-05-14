# Demos

Each subdirectory pairs a **marimo notebook** (`.py` app on disk) with the **Cursor session transcript** used while building it.

| Folder | Notebook | Chat log |
|--------|----------|----------|
| [`dry-run/`](dry-run/) | [`hackathon-demo.py`](dry-run/hackathon-demo.py) | [`cursor-chat-f20cbaac.md`](dry-run/cursor-chat-f20cbaac.md) |
| [`live-run/`](live-run/) | [`demo.py`](live-run/demo.py) | [`session-log.md`](live-run/session-log.md) |

Run marimo from the **repository root** (recommended). Both notebooks resolve `data/` via `Path(__file__).resolve().parent.parent.parent` so CSV and PDB paths stay correct under `demos/`.
