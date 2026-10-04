"""Offline verification of the released files and the paper's derived results.

1. Every file matches SHA256SUMS.
2. The main analysis tables are recomputed from merged_runs.csv.
3. The Figure 2 intervals, the Figure 2 table and both figures are rebuilt
   in a temporary directory.
4. Deterministic simulator cells are rerun and compared with the run records.

No network access or API key is used. Released files are never modified.
"""

from __future__ import annotations

import csv
import hashlib
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LLM = ROOT / "docs/results/execution_sensitivity_llm"
TABLES = ("merged_aggregate.csv", "rank_stability.csv", "fragility_did.csv", "sampling_variance.csv")
RERUN_AGENTS = "buy-and-hold,risk-parity,naive-momentum,mean-reversion"
RERUN_LEVELS = "E0_ideal,E1_default_stress,E2_harsh_corner"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(*args: str) -> None:
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"), PYTHONDONTWRITEBYTECODE="1")
    result = subprocess.run([sys.executable, "-B", *args], cwd=ROOT, env=env, capture_output=True, text=True)
    if result.returncode:
        raise SystemExit(f"command failed: {' '.join(args)}\n{result.stdout}\n{result.stderr}")


def same_text(a: Path, b: Path) -> bool:
    return a.read_bytes().replace(b"\r\n", b"\n") == b.read_bytes().replace(b"\r\n", b"\n")


def check_manifest() -> None:
    expected = {}
    for line in (ROOT / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        sha, rel = line.split("  ", 1)
        expected[rel] = sha
    actual = {p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*")
              if p.is_file() and ".git" not in p.relative_to(ROOT).parts
              and "__pycache__" not in p.parts and p.name != "SHA256SUMS"}
    missing, extra = sorted(set(expected) - actual), sorted(actual - set(expected))
    bad = [rel for rel in sorted(set(expected) & actual) if digest(ROOT / rel) != expected[rel]]
    if missing or bad:
        raise SystemExit(f"manifest check failed: missing={missing[:5]} changed={bad[:5]}")
    note = f" ({len(extra)} untracked local files ignored)" if extra else ""
    print(f"PASS {len(expected)} files match SHA256SUMS{note}")


def check_tables(tmp: Path) -> None:
    out = tmp / "analysis"
    run("scripts/analyze_execution_sensitivity_llm.py", "--merged-runs", str(LLM / "merged_runs.csv"),
        "--output-dir", str(out))
    for name in TABLES:
        if not same_text(out / name, LLM / name):
            raise SystemExit(f"recomputed table differs: {name}")
    print(f"PASS {len(TABLES)} analysis tables recomputed from merged_runs.csv")


def check_tau_cis(tmp: Path) -> None:
    out = tmp / "tau_curve_cis.csv"
    code = ("import sys; from pathlib import Path; sys.path[:0] = ['scripts', 'src']; "
            "import build_tau_curve_cis as b; b.OUT = Path(sys.argv[1]); b.main()")
    run("-c", code, str(out))
    released = ROOT / "docs/results/execution_sensitivity_scaffold/tau_curve_cis.csv"
    if not same_text(out, released):
        raise SystemExit("horizon and universe interval table differs from the released table")
    print("PASS Figure 2 horizon and universe intervals rebuilt from run records")


def check_figures(tmp: Path) -> None:
    table = tmp / "robustness_curves.csv"
    run("scripts/build_robustness_figure.py", "--table", str(table), "--figure", str(tmp / "robustness_curves.pdf"))
    released = ROOT / "docs/results/execution_sensitivity_scaffold/robustness_curves.csv"
    if not same_text(table, released):
        raise SystemExit("Figure 2 table differs from the released table")
    run("scripts/render_execution_sensitivity_figures.py", "--input-dir", str(LLM), "--output-dir", str(tmp))
    for name in ("tau_heatmap.pdf", "robustness_curves.pdf"):
        if not (tmp / name).is_file():
            raise SystemExit(f"figure not produced: {name}")
    print("PASS Figure 2 table rebuilt identically; Figures 1 and 2 rendered")


def check_rerun(tmp: Path) -> None:
    out = tmp / "rerun"
    run("scripts/run_execution_sensitivity_sweep.py", "--agents", RERUN_AGENTS, "--scenarios", "high_vol",
        "--seeds", "1,2", "--periods", "12", "--levels", RERUN_LEVELS, "--output-dir", str(out))
    with (LLM / "merged_runs.csv").open(encoding="utf-8") as handle:
        released = {(r["level"], r["agent"], r["seed"]): r for r in csv.DictReader(handle)
                    if r["scenario"] == "high_vol"}
    with (out / "execution_sensitivity_runs.csv").open(encoding="utf-8") as handle:
        rerun = list(csv.DictReader(handle))
    fields = ("total_return", "sharpe", "max_drawdown", "execution_fill_rate")
    for row in rerun:
        ref = released[(row["level"], row["agent"], row["seed"])]
        if any(abs(float(row[f]) - float(ref[f])) > 1e-12 for f in fields):
            raise SystemExit(f"deterministic rerun differs: {row['level']} {row['agent']} seed {row['seed']}")
    print(f"PASS {len(rerun)} deterministic simulator runs reproduce the released records")


def main() -> int:
    check_manifest()
    with tempfile.TemporaryDirectory() as tmp:
        check_tables(Path(tmp))
        check_tau_cis(Path(tmp))
        check_figures(Path(tmp))
        check_rerun(Path(tmp))
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
