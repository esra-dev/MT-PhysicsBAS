# Test A — toggling micro-mechanism audit (registered 2026-07-18c §1)

**Decision: INDETERMINATE (insufficient toggling to instrument)**

| item | value | pass |
|---|---|---|
| G1 instrument reconciliation | ql_true 800/800 (1.0000), ql_false 800/800 (1.0000) | True |
| G2 encoding/selection consistency | pooled 1885/1885 (1.0000); unmappable 0 | True |
| G3 init determinism | bit-identical A/B: True | True |
| minimum data (>= 20 pairs) | 13 pooled unique KG-arm greedy toggle pairs | False |
| S1 greedy share of toggles | 1.0000 (D3 545 / D2 545) | True |
| P1 median toggle-pair visits | 159 (<= 5); non-toggle descriptive 194 (n=9) | False |
| P2 init alignment | rate 1.0000 vs chance 0.2727+0.2 = 0.4727, MC p = 9.99990000099999e-06 | True |
| P3 tabula-rasa control | rate 0.07692307692307693 vs chance 0.2727272727272727, p = 0.983990160098399; excluded 0/13, decidable 13; indeterminate = True; control_aligns = False | False |

Event tallies: {"ql_true": {"D1_flips": 1050, "D2_toggles": 545, "D3_greedy_toggles": 545, "toggle_stuck_split": {"stuck": 0, "greedy": 545}}, "ql_false": {"D1_flips": 455, "D2_toggles": 90, "D3_greedy_toggles": 90, "toggle_stuck_split": {"stuck": 0, "greedy": 90}}}

Cycling-delta decomposition (descriptive): {"D1_flip_delta_true_minus_false": 595, "D2_toggle_delta_true_minus_false": 455, "toggle_share_of_delta": 0.7647058823529411}
