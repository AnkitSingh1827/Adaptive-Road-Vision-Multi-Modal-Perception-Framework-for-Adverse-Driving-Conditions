import sys
import time
from pathlib import Path

# Ensure UTF-8 output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

scripts_dir = Path(__file__).resolve().parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from run_notebook import run_notebook

def main():
    root = scripts_dir.parent
    notebooks = [
        "notebooks/08_cyclegan_fog_generation.ipynb",
        "notebooks/09_synthetic_fog_quality_check.ipynb",
        "notebooks/10_final_dataset_creation.ipynb",
        "notebooks/11_data_preprocessing.ipynb",
    ]

    print("\n" + "=" * 70)
    print("STARTING SEQUENTIAL EXECUTION: NOTEBOOKS 08 -> 11")
    print("=" * 70)
    start_all = time.time()

    for nb_rel in notebooks:
        nb_path = root / nb_rel
        print(f"\n>>> Running: {nb_rel} ...")
        t0 = time.time()
        run_notebook(str(nb_path))
        print(f">>> Finished: {nb_rel} in {time.time() - t0:.2f}s\n")

    total_time = time.time() - start_all
    print("=" * 70)
    print(f"PIPELINE COMPLETED SUCCESSFULLY in {total_time:.2f}s ({total_time / 60:.2f} minutes)!")
    print("=" * 70)

if __name__ == "__main__":
    main()
