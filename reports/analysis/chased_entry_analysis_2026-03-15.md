# Chased Entry Analysis

- Generated: 2026-03-15T22:11:49Z
- Runs analyzed: 7
- Total candidates: 147
- Source files: 2026-03-09.json, 2026-03-10.json, 2026-03-11.json, 2026-03-12.json, 2026-03-13.json, 2026-03-14.json, 2026-03-15.json

## Overall entry-state counts

- chased: 116
- late: 18
- early: 13

## Overall decision counts

- NO_TRADE: 127
- WAIT: 19
- ENTER: 1

## Per-run chased summary

| Date | Candidates | Chased | Chased % | Median chased distance % | P75 chased distance % | Pullback count | Reversal count | Breakout count | Other count |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2026-03-09 | 21 | 16 | 76.19 | 16.59 | 26.60 | 8 | 11 | 0 | 2 |
| 2026-03-10 | 21 | 18 | 85.71 | 10.48 | 17.34 | 4 | 11 | 0 | 6 |
| 2026-03-11 | 21 | 13 | 61.90 | 12.26 | 27.08 | 9 | 11 | 0 | 1 |
| 2026-03-12 | 21 | 16 | 76.19 | 11.67 | 14.33 | 6 | 11 | 0 | 4 |
| 2026-03-13 | 21 | 18 | 85.71 | 6.81 | 11.94 | 1 | 9 | 2 | 9 |
| 2026-03-14 | 21 | 18 | 85.71 | 9.18 | 15.82 | 5 | 9 | 3 | 4 |
| 2026-03-15 | 21 | 17 | 80.95 | 12.01 | 14.57 | 8 | 8 | 2 | 3 |

## Setup breakdown

| Setup | Bucket | Candidates | Chased | Chased % | Median distance % | P75 distance % |
|---|---|---:|---:|---:|---:|---:|
| breakout_immediate_1_5d | breakout | 2 | 2 | 100.00 | 9.52 | 10.05 |
| breakout_retest_1_5d | breakout | 5 | 5 | 100.00 | 19.86 | 21.70 |
|  | other | 29 | 27 | 93.10 | 7.27 | 14.57 |
|  | pullback | 41 | 24 | 58.54 | 5.17 | 13.56 |
|  | reversal | 70 | 58 | 82.86 | 9.14 | 16.05 |

## Most common decision reasons

- risk_reward_unattractive: 125
- tradeability_marginal: 122
- entry_chased: 109
- btc_regime_caution: 46
- entry_not_confirmed: 46
- retest_not_reclaimed: 39
- entry_late: 18
- entry_too_early: 13
- rebound_not_confirmed: 7
- price_past_target_1: 2

## Sample chased candidates (overall)

| Date | Symbol | Decision | Setup | Bucket | Distance % | Reasons |
|---|---|---|---|---|---:|---|
| 2026-03-09 | QUBICUSDT | NO_TRADE |  | reversal | 37.40 | tradeability_marginal, risk_reward_unattractive, entry_chased |
| 2026-03-09 | NAORISUSDT | NO_TRADE |  | other | 34.08 | tradeability_marginal, risk_reward_unattractive, entry_chased |
| 2026-03-09 | RESOLVUSDT | NO_TRADE |  | pullback | 28.36 | tradeability_marginal, risk_reward_unattractive, entry_chased |
| 2026-03-09 | BABYUSDT | NO_TRADE |  | reversal | 26.60 | tradeability_marginal, risk_reward_unattractive |
| 2026-03-09 | BABYUSDT | NO_TRADE |  | reversal | 26.60 | tradeability_marginal, risk_reward_unattractive, entry_chased |
| 2026-03-09 | CVXUSDT | NO_TRADE |  | reversal | 20.30 | tradeability_marginal, risk_reward_unattractive, entry_chased |
| 2026-03-09 | PLUMEUSDT | NO_TRADE |  | reversal | 19.00 | tradeability_marginal, risk_reward_unattractive, btc_regime_caution, entry_chased |
| 2026-03-09 | KAVAUSDT | NO_TRADE |  | other | 17.63 | tradeability_marginal, risk_reward_unattractive, entry_chased |
| 2026-03-09 | OKBUSDT | NO_TRADE |  | reversal | 15.54 | tradeability_marginal, risk_reward_unattractive, entry_chased |
| 2026-03-09 | HYPEUSDT | NO_TRADE |  | reversal | 15.48 | tradeability_marginal, risk_reward_unattractive, btc_regime_caution, entry_chased |
| 2026-03-09 | DEXEUSDT | NO_TRADE |  | pullback | 13.79 | tradeability_marginal, risk_reward_unattractive, entry_chased |
| 2026-03-09 | ZROUSDT | NO_TRADE |  | reversal | 11.84 | risk_reward_unattractive, entry_chased |
| 2026-03-09 | ETHFIUSDT | NO_TRADE |  | reversal | 10.23 | tradeability_marginal, risk_reward_unattractive, entry_not_confirmed, retest_not_reclaimed, entry_chased |
| 2026-03-09 | SIGNUSDT | NO_TRADE |  | pullback | 8.17 | tradeability_marginal, risk_reward_unattractive, entry_chased |
| 2026-03-09 | HUMAUSDT | NO_TRADE |  | reversal | 6.80 | tradeability_marginal, risk_reward_unattractive, btc_regime_caution, entry_chased |
| 2026-03-09 | COWUSDT | NO_TRADE |  | pullback | 4.25 | tradeability_marginal, risk_reward_unattractive, entry_chased |
| 2026-03-10 | FLOWUSDT | NO_TRADE |  | reversal | 67.49 | tradeability_marginal, risk_reward_unattractive, btc_regime_caution, entry_not_confirmed, retest_not_reclaimed, entry_chased |
| 2026-03-10 | PIXELUSDT | NO_TRADE |  | other | 56.06 | tradeability_marginal, risk_reward_unattractive, btc_regime_caution, entry_not_confirmed, retest_not_reclaimed, entry_chased |
| 2026-03-10 | ARIAUSDT | NO_TRADE |  | pullback | 37.31 | tradeability_marginal, risk_reward_unattractive, btc_regime_caution, entry_chased |
| 2026-03-10 | KERNELUSDT | NO_TRADE |  | other | 19.30 | tradeability_marginal, risk_reward_unattractive, entry_chased |

## Pullback only

- Candidates: 41

### Entry-state counts

- chased: 24
- late: 8
- early: 9

### Decision counts

- NO_TRADE: 33
- WAIT: 8

### Per-run summary

| Date | Candidates | Chased | Chased % | Median chased distance % | P75 chased distance % |
|---|---:|---:|---:|---:|---:|
| 2026-03-09 | 8 | 4 | 50.00 | 10.98 | 17.43 |
| 2026-03-10 | 4 | 3 | 75.00 | 8.50 | 22.91 |
| 2026-03-11 | 9 | 3 | 33.33 | 26.51 | 41.63 |
| 2026-03-12 | 6 | 4 | 66.67 | 9.90 | 12.70 |
| 2026-03-13 | 1 | 1 | 100.00 | 4.48 | 4.48 |
| 2026-03-14 | 5 | 4 | 80.00 | 18.33 | 20.88 |
| 2026-03-15 | 8 | 5 | 62.50 | 13.53 | 15.01 |

### Most common decision reasons

- tradeability_marginal: 37
- risk_reward_unattractive: 33
- entry_chased: 24
- btc_regime_caution: 12
- entry_too_early: 9
- entry_late: 8
- entry_not_confirmed: 6
- rebound_not_confirmed: 6

### Sample chased candidates

| Date | Symbol | Decision | Setup | Bucket | Distance % | Reasons |
|---|---|---|---|---|---:|---|
| 2026-03-09 | RESOLVUSDT | NO_TRADE |  | pullback | 28.36 | tradeability_marginal, risk_reward_unattractive, entry_chased |
| 2026-03-09 | DEXEUSDT | NO_TRADE |  | pullback | 13.79 | tradeability_marginal, risk_reward_unattractive, entry_chased |
| 2026-03-09 | SIGNUSDT | NO_TRADE |  | pullback | 8.17 | tradeability_marginal, risk_reward_unattractive, entry_chased |
| 2026-03-09 | COWUSDT | NO_TRADE |  | pullback | 4.25 | tradeability_marginal, risk_reward_unattractive, entry_chased |
| 2026-03-10 | ARIAUSDT | NO_TRADE |  | pullback | 37.31 | tradeability_marginal, risk_reward_unattractive, btc_regime_caution, entry_chased |
| 2026-03-10 | GRASSUSDT | NO_TRADE |  | pullback | 8.50 | tradeability_marginal, risk_reward_unattractive, entry_chased |
| 2026-03-10 | PIUSDT | NO_TRADE |  | pullback | 5.10 | tradeability_marginal, risk_reward_unattractive, entry_chased |
| 2026-03-11 | PIXELUSDT | NO_TRADE |  | pullback | 56.76 | tradeability_marginal, risk_reward_unattractive, btc_regime_caution, entry_chased |
| 2026-03-11 | ARIAUSDT | NO_TRADE |  | pullback | 26.51 | tradeability_marginal, risk_reward_unattractive, entry_chased |
| 2026-03-11 | GRASSUSDT | NO_TRADE |  | pullback | 8.60 | tradeability_marginal, risk_reward_unattractive, entry_chased |

## Reversal only

- Candidates: 70

### Entry-state counts

- chased: 58
- late: 8
- early: 4

### Decision counts

- NO_TRADE: 64
- WAIT: 6

### Per-run summary

| Date | Candidates | Chased | Chased % | Median chased distance % | P75 chased distance % |
|---|---:|---:|---:|---:|---:|
| 2026-03-09 | 11 | 10 | 90.91 | 17.27 | 25.02 |
| 2026-03-10 | 11 | 9 | 81.82 | 12.46 | 17.34 |
| 2026-03-11 | 11 | 9 | 81.82 | 12.26 | 27.08 |
| 2026-03-12 | 11 | 9 | 81.82 | 11.88 | 16.00 |
| 2026-03-13 | 9 | 7 | 77.78 | 11.07 | 15.62 |
| 2026-03-14 | 9 | 7 | 77.78 | 5.39 | 8.36 |
| 2026-03-15 | 8 | 7 | 87.50 | 12.01 | 14.21 |

### Most common decision reasons

- risk_reward_unattractive: 62
- tradeability_marginal: 58
- entry_chased: 54
- entry_not_confirmed: 27
- retest_not_reclaimed: 27
- btc_regime_caution: 25
- entry_late: 8
- entry_too_early: 4
- price_past_target_1: 2

### Sample chased candidates

| Date | Symbol | Decision | Setup | Bucket | Distance % | Reasons |
|---|---|---|---|---|---:|---|
| 2026-03-09 | QUBICUSDT | NO_TRADE |  | reversal | 37.40 | tradeability_marginal, risk_reward_unattractive, entry_chased |
| 2026-03-09 | BABYUSDT | NO_TRADE |  | reversal | 26.60 | tradeability_marginal, risk_reward_unattractive |
| 2026-03-09 | BABYUSDT | NO_TRADE |  | reversal | 26.60 | tradeability_marginal, risk_reward_unattractive, entry_chased |
| 2026-03-09 | CVXUSDT | NO_TRADE |  | reversal | 20.30 | tradeability_marginal, risk_reward_unattractive, entry_chased |
| 2026-03-09 | PLUMEUSDT | NO_TRADE |  | reversal | 19.00 | tradeability_marginal, risk_reward_unattractive, btc_regime_caution, entry_chased |
| 2026-03-09 | OKBUSDT | NO_TRADE |  | reversal | 15.54 | tradeability_marginal, risk_reward_unattractive, entry_chased |
| 2026-03-09 | HYPEUSDT | NO_TRADE |  | reversal | 15.48 | tradeability_marginal, risk_reward_unattractive, btc_regime_caution, entry_chased |
| 2026-03-09 | ZROUSDT | NO_TRADE |  | reversal | 11.84 | risk_reward_unattractive, entry_chased |
| 2026-03-09 | ETHFIUSDT | NO_TRADE |  | reversal | 10.23 | tradeability_marginal, risk_reward_unattractive, entry_not_confirmed, retest_not_reclaimed, entry_chased |
| 2026-03-09 | HUMAUSDT | NO_TRADE |  | reversal | 6.80 | tradeability_marginal, risk_reward_unattractive, btc_regime_caution, entry_chased |

## Breakout only

- Candidates: 7

### Entry-state counts

- chased: 7

### Decision counts

- NO_TRADE: 7

### Per-run summary

| Date | Candidates | Chased | Chased % | Median chased distance % | P75 chased distance % |
|---|---:|---:|---:|---:|---:|
| 2026-03-13 | 2 | 2 | 100.00 | 16.97 | 19.33 |
| 2026-03-14 | 3 | 3 | 100.00 | 10.57 | 15.22 |
| 2026-03-15 | 2 | 2 | 100.00 | 22.81 | 29.99 |

### Most common decision reasons

- risk_reward_unattractive: 7
- entry_chased: 4
- tradeability_marginal: 3

### Sample chased candidates

| Date | Symbol | Decision | Setup | Bucket | Distance % | Reasons |
|---|---|---|---|---|---:|---|
| 2026-03-13 | TAOUSDT | NO_TRADE | breakout_retest_1_5d | breakout | 21.70 | risk_reward_unattractive, entry_chased |
| 2026-03-13 | TAOUSDT | NO_TRADE | breakout_retest_1_5d | breakout | 12.23 | risk_reward_unattractive |
| 2026-03-14 | FETUSDT | NO_TRADE | breakout_retest_1_5d | breakout | 19.86 | risk_reward_unattractive |
| 2026-03-14 | FETUSDT | NO_TRADE | breakout_immediate_1_5d | breakout | 10.57 | risk_reward_unattractive, entry_chased |
| 2026-03-14 | JSTUSDT | NO_TRADE | breakout_retest_1_5d | breakout | 4.28 | tradeability_marginal, risk_reward_unattractive, entry_chased |
| 2026-03-15 | SPKUSDT | NO_TRADE | breakout_retest_1_5d | breakout | 37.16 | tradeability_marginal, risk_reward_unattractive |
| 2026-03-15 | SPKUSDT | NO_TRADE | breakout_immediate_1_5d | breakout | 8.47 | tradeability_marginal, risk_reward_unattractive, entry_chased |

## Other only

- Candidates: 29

### Entry-state counts

- chased: 27
- late: 2

### Decision counts

- NO_TRADE: 23
- WAIT: 5
- ENTER: 1

### Per-run summary

| Date | Candidates | Chased | Chased % | Median chased distance % | P75 chased distance % |
|---|---:|---:|---:|---:|---:|
| 2026-03-09 | 2 | 2 | 100.00 | 25.85 | 29.96 |
| 2026-03-10 | 6 | 6 | 100.00 | 10.99 | 18.23 |
| 2026-03-11 | 1 | 1 | 100.00 | 5.77 | 5.77 |
| 2026-03-12 | 4 | 3 | 75.00 | 11.46 | 18.45 |
| 2026-03-13 | 9 | 8 | 88.89 | 5.78 | 6.59 |
| 2026-03-14 | 4 | 4 | 100.00 | 11.55 | 15.39 |
| 2026-03-15 | 3 | 3 | 100.00 | 5.59 | 10.08 |

### Most common decision reasons

- entry_chased: 27
- tradeability_marginal: 24
- risk_reward_unattractive: 23
- entry_not_confirmed: 13
- retest_not_reclaimed: 12
- btc_regime_caution: 9
- entry_late: 2
- rebound_not_confirmed: 1

### Sample chased candidates

| Date | Symbol | Decision | Setup | Bucket | Distance % | Reasons |
|---|---|---|---|---|---:|---|
| 2026-03-09 | NAORISUSDT | NO_TRADE |  | other | 34.08 | tradeability_marginal, risk_reward_unattractive, entry_chased |
| 2026-03-09 | KAVAUSDT | NO_TRADE |  | other | 17.63 | tradeability_marginal, risk_reward_unattractive, entry_chased |
| 2026-03-10 | PIXELUSDT | NO_TRADE |  | other | 56.06 | tradeability_marginal, risk_reward_unattractive, btc_regime_caution, entry_not_confirmed, retest_not_reclaimed, entry_chased |
| 2026-03-10 | KERNELUSDT | NO_TRADE |  | other | 19.30 | tradeability_marginal, risk_reward_unattractive, entry_chased |
| 2026-03-10 | ETHFIUSDT | NO_TRADE |  | other | 15.03 | tradeability_marginal, risk_reward_unattractive, btc_regime_caution, entry_chased |
| 2026-03-10 | JSTUSDT | NO_TRADE |  | other | 6.94 | tradeability_marginal, risk_reward_unattractive, btc_regime_caution, entry_chased |
| 2026-03-10 | SUIUSDT | NO_TRADE |  | other | 4.40 | risk_reward_unattractive, btc_regime_caution, entry_not_confirmed, retest_not_reclaimed, entry_chased |
| 2026-03-10 | UNIUSDT | NO_TRADE |  | other | 3.01 | tradeability_marginal, risk_reward_unattractive, btc_regime_caution, entry_not_confirmed, retest_not_reclaimed, entry_chased |
| 2026-03-11 | PIUSDT | NO_TRADE |  | other | 5.77 | tradeability_marginal, risk_reward_unattractive, entry_not_confirmed, rebound_not_confirmed, entry_chased |
| 2026-03-12 | FLOWUSDT | NO_TRADE |  | other | 25.43 | tradeability_marginal, risk_reward_unattractive, entry_not_confirmed, retest_not_reclaimed, entry_chased |

