"""Seed-cluster bootstrap helpers for board-level Kendall tau.

Cell value = mean Sharpe over seeds; Kendall tau_b between two level boards;
95% interval from resampling seeds with replacement (10,000 draws, fixed RNG).
"""
from __future__ import annotations

import csv
import random
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tradearena.evaluation.statistics import kendall_tau

DRAWS = 10_000


def load_runs(dirs: tuple[Path, ...]) -> dict[str, dict[str, dict[str, dict[int, float]]]]:
    """scenario -> level -> agent -> seed -> sharpe (sample-0 rows, deduped)."""
    table: dict[str, dict[str, dict[str, dict[int, float]]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(dict))
    )
    for d in dirs:
        path = d / "execution_sensitivity_runs.csv"
        if not path.exists():
            continue
        with path.open(encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                if int(row.get("sample", 0) or 0) != 0:
                    continue
                table[row["scenario"]][row["level"]][row["agent"]][int(row["seed"])] = float(
                    row["sharpe"]
                )
    return table


def board_tau(
    level_a: dict[str, dict[int, float]],
    level_b: dict[str, dict[int, float]],
    agents: list[str],
    seeds: list[int],
) -> float:
    mean_a = {a: sum(level_a[a][s] for s in seeds) / len(seeds) for a in agents}
    mean_b = {a: sum(level_b[a][s] for s in seeds) / len(seeds) for a in agents}
    tau = kendall_tau(mean_a, mean_b)
    return 0.0 if tau is None else tau


def tau_with_ci(
    level_a: dict[str, dict[int, float]],
    level_b: dict[str, dict[int, float]],
) -> tuple[int, int, float, float, float] | None:
    agents = sorted(set(level_a) & set(level_b))
    seeds: list[int] = []
    if agents:
        shared: set[int] = set(level_a[agents[0]])
        for a in agents:
            shared &= set(level_a[a])
            shared &= set(level_b[a])
        seeds = sorted(shared)
    if len(agents) < 4 or len(seeds) < 3:
        return None
    point = board_tau(level_a, level_b, agents, seeds)
    rng = random.Random(20260717)
    draws = sorted(
        board_tau(level_a, level_b, agents, [rng.choice(seeds) for _ in seeds])
        for _ in range(DRAWS)
    )
    return len(agents), len(seeds), point, draws[int(0.025 * DRAWS)], draws[int(0.975 * DRAWS)]
