import marimo._code_mode as cm
from pathlib import Path

root = Path("/home/frank/Tech/2026-pydata-boston-cursor-hackathon")
full = (root / "scripts/marimo_vat_apply.py").read_text()
body = full.split('PLOT = """', 1)[1].split('"""', 1)[0]


async def main():
    async with cm.get_context() as ctx:
        ctx.edit_cell("plot_actual_vs_cf", code=body)
        cid = next(i for i, c in ctx.cells.items() if getattr(c, "name", None) == "plot_actual_vs_cf")
        ctx.run_cell(cid)


await main()
