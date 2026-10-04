# Execution Assumptions and Short-Horizon Sharpe Rankings

Code and data for the paper:

> Weicheng Xue. How Execution Assumptions Change Short-Horizon Sharpe Rankings: Evidence from a Synthetic Trading Benchmark. arXiv preprint, 2026.

The study compares the same trading policies on the same synthetic price paths
under six execution settings and measures how much the leaderboard reorders.
This repository contains the run-level records behind every table and figure,
the analysis and figure scripts, the simulator code needed to rerun the
deterministic experiments, and an offline verifier.

## Quick start

Python 3.11 or newer (tested with 3.12). No network access or API key is needed.

```text
python -m pip install -r requirements.txt
python verify_artifact.py
python -m pytest
```

To recompute saved analyses and figures without running new simulator cases:

```text
python verify_artifact.py --analysis-only
```

`verify_artifact.py` checks every file against `SHA256SUMS`, recomputes the
main analysis tables from `merged_runs.csv`, rebuilds the Figure 2 intervals,
the Figure 2 table and both figures in a temporary directory, and reruns a set
of deterministic simulator cells and compares them with the released run
records.

## Where each result comes from

| Paper item | Released records | Script |
|---|---|---|
| Figure 1 | `execution_sensitivity_llm/rank_stability.csv` | `render_execution_sensitivity_figures.py` |
| Figure 2 | `execution_sensitivity_scaffold/robustness_curves.csv`, `tau_curve_cis.csv` | `build_robustness_figure.py`, `build_tau_curve_cis.py` |
| Tables 2 and 3 | `execution_sensitivity_llm/merged_aggregate.csv`, `fragility_did.csv` | `analyze_execution_sensitivity_llm.py` |
| Sampling variance | `execution_sensitivity_llm/sampling_variance.csv` | `analyze_execution_sensitivity_llm.py` |
| Turnover control | `execution_sensitivity_llm/turnover_control.csv`, `execution_sensitivity_costaware/` | `analyze_turnover_control.py`, `analyze_costaware_baseline.py` |
| Universe size and horizon | `execution_sensitivity_N3/`, `_N5/`, `_universe10*/`, `_b1_horizon/`, `_horizon_universe/` | `analyze_horizon_and_universe.py`, `analyze_universe10.py`, `build_universe10_ladder_taus.py` |
| Buy-and-hold anchor | `execution_sensitivity_anchor/` | `run_anchor_robustness.py` |
| Capital scale | `execution_sensitivity_capital_scale/` | `analyze_capital_scale.py` |
| Parameter grid | `execution_sensitivity_grid/` | `run_execution_param_grid.py` |
| Real-price check | `execution_sensitivity_real/`, `execution_sensitivity_real_etf/` | `run_execution_sensitivity_real.py` |
| Open-loop replay | `execution_sensitivity_b7_openloop/` | `run_b7_openloop.py` |

All result folders are under `docs/results/`; all scripts are under `scripts/`.

## What can be reproduced

- **Tables and figures** are rebuilt from the frozen run-level records without
  any API call.
- **Deterministic experiments** can be rerun from the start. For example:

  ```text
  python scripts/run_execution_sensitivity_sweep.py --agents buy-and-hold,risk-parity \
    --scenarios high_vol --seeds 1,2,3,4,5,6,7,8,9,10 --periods 12 \
    --levels E0_ideal,E1_default_stress --output-dir outputs/rerun
  ```

  Seeds are given per scenario; the script adds the scenario offset itself.
- **LLM rows** need provider access (`DEEPSEEK_API_KEY` for the direct model,
  `POE_API_KEY` for the routed aliases). Four of the five LLM policies used
  provider-routed aliases. The direct API identifier is also undated and does
  not pin an immutable backend, so a fresh
  collection will not reproduce the recorded responses byte for byte. Raw
  provider responses and per-step trajectories are not included.
- **Real-price check.** Yahoo Finance data are not redistributed. Download daily
  OHLCV files with `scripts/download_yahoo_daily.py`, then pass the folder and
  symbols to `run_execution_sensitivity_real.py`.

`sampling_variance.csv` includes repeat coverage for every reported cell.
Under independent errors with a common within-seed variance, let W be the mean
sample variance of seeds with repeats, V the sample variance of all seed means,
and n_s the sample count for seed s. The estimate is
B = max(0, V - W * mean(1/n_s)), including singleton seeds in the correction;
the estimated share is W/(B+W). Truncation and sparse repeat coverage make this
ratio uncertain. The paper summarizes only the 14 balanced cells with three
samples at each of ten seeds (`summary_eligible=True`). Four uneven cells are
retained for inspection, including two with only one repeated seed. This is a
descriptive decomposition, not an identified causal contribution of sampling.

## License

Code is released under the MIT License in `LICENSE`.
