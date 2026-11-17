import sys
import json
import time
import io
import traceback
from pathlib import Path
from contextlib import redirect_stdout, redirect_stderr

# Ensure Windows terminal doesn't crash on Unicode characters like arrows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from IPython.core.interactiveshell import InteractiveShell

def run_notebook(nb_path: str):
    nb_file = Path(nb_path).resolve()
    print(f"\n=======================================================")
    print(f"Executing Notebook: {nb_file.name}")
    print(f"=======================================================")

    with open(nb_file, "r", encoding="utf-8") as f:
        nb_data = json.load(f)

    # Initialize / reset shell instance
    shell = InteractiveShell.instance()
    shell.reset()

    # Ensure display works properly in console
    def custom_display(*args, **kwargs):
        for arg in args:
            if hasattr(arg, "to_string"):
                print(arg.to_string())
            else:
                print(arg)
    shell.user_ns["display"] = custom_display

    code_cells = [c for c in nb_data.get("cells", []) if c.get("cell_type") == "code"]
    total_code = len(code_cells)
    print(f"Total cells: {len(nb_data.get('cells', []))} ({total_code} code cells)")

    exec_count = 0
    start_total = time.time()

    for idx, cell in enumerate(nb_data.get("cells", [])):
        if cell.get("cell_type") != "code":
            continue

        exec_count += 1
        src = "".join(cell.get("source", []))
        if not src.strip():
            cell["execution_count"] = exec_count
            cell["outputs"] = []
            continue

        first_line = src.strip().split("\n")[0][:70]
        print(f"\n[Cell {idx+1} | Code {exec_count}/{total_code}] {first_line} ...", flush=True)

        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()
        cell_start = time.time()

        with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
            result = shell.run_cell(src, store_history=True)

        cell_elapsed = time.time() - cell_start
        out_str = stdout_buf.getvalue()
        err_str = stderr_buf.getvalue()

        if out_str:
            print(out_str.rstrip())
        if err_str:
            print(f"[STDERR]\n{err_str.rstrip()}", file=sys.stderr)

        # Build Jupyter cell outputs
        outputs = []
        if out_str:
            outputs.append({
                "output_type": "stream",
                "name": "stdout",
                "text": out_str.splitlines(keepends=True)
            })
        if err_str:
            outputs.append({
                "output_type": "stream",
                "name": "stderr",
                "text": err_str.splitlines(keepends=True)
            })

        if result.error_in_exec:
            ename = type(result.error_in_exec).__name__
            evalue = str(result.error_in_exec)
            tb = traceback.format_tb(result.error_in_exec.__traceback__)
            outputs.append({
                "output_type": "error",
                "ename": ename,
                "evalue": evalue,
                "traceback": tb
            })
            cell["execution_count"] = exec_count
            cell["outputs"] = outputs

            # Save notebook before raising
            with open(nb_file, "w", encoding="utf-8") as f:
                json.dump(nb_data, f, indent=1, ensure_ascii=False)

            print(f"\n[ERROR] Cell {idx+1} failed with {ename}: {evalue}", file=sys.stderr)
            raise result.error_in_exec

        if result.result is not None:
            outputs.append({
                "output_type": "execute_result",
                "execution_count": exec_count,
                "data": {
                    "text/plain": repr(result.result)
                },
                "metadata": {}
            })
            print(repr(result.result))

        cell["execution_count"] = exec_count
        cell["outputs"] = outputs
        print(f" -> Completed in {cell_elapsed:.2f}s", flush=True)

    total_elapsed = time.time() - start_total
    with open(nb_file, "w", encoding="utf-8") as f:
        json.dump(nb_data, f, indent=1, ensure_ascii=False)

    print(f"\n[SUCCESS] Notebook {nb_file.name} completed in {total_elapsed:.2f}s. Saved outputs.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/run_notebook.py <path_to_notebook.ipynb>")
        sys.exit(1)
    run_notebook(sys.argv[1])
