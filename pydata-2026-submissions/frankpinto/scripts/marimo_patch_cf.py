import marimo._code_mode as cm
from pathlib import Path

root = Path("/home/frank/Tech/2026-pydata-boston-cursor-hackathon")
full = (root / "scripts/marimo_vat_apply.py").read_text()
_a = full.split('MODEL_CF = """', 1)[1]
body = _a.split('"""\n\nVALIDATION', 1)[0]


async def main():
    async with cm.get_context() as ctx:
        ctx.edit_cell("counterfactual_model", code=body)
        for n in ("counterfactual_model", "validation_summary", "plot_actual_vs_cf"):
            cid = next(i for i, c in ctx.cells.items() if getattr(c, "name", None) == n)
            ctx.run_cell(cid)


await main()
