# Turnover-Controlled Ranking Stability

Agents are binned into terciles by realized E1 turnover, and the E0-vs-E1
Kendall tau is recomputed within each tercile. Each tercile holds four
agents, so within-bin values are coarse and are not directly comparable
with the full-leaderboard tau.

| Regime | Turnover bin | Mean turnover | Within-bin tau (E0 vs E1) | Full-leaderboard tau |
| --- | --- | ---: | ---: | ---: |
| calm | T1 | 10.5 | 1.0 | 0.818 |
| calm | T2 | 18.73 | 0.667 | 0.818 |
| calm | T3 | 20.25 | 0.333 | 0.818 |
| high_vol | T1 | 11.53 | 0.667 | 0.212 |
| high_vol | T2 | 17.48 | 0.667 | 0.212 |
| high_vol | T3 | 19.52 | 0.667 | 0.212 |
| jump_tail | T1 | 11.43 | 0.667 | 0.515 |
| jump_tail | T2 | 17.85 | 0.0 | 0.515 |
| jump_tail | T3 | 19.75 | 1.0 | 0.515 |

Mean within-bin tau across all regimes and terciles: **0.630**.
