# Preload on or off, same session - 2026-11-08 19:17

`python tools/startup_check.py --trials 3`: trials alternate off and on, each with a fresh server for the broken-model case and another for the healthy case. Times are client-side wall clock.

| Measure | Preload off (each trial) | Off mean | Preload on (each trial) | On mean |
|---|---|---|---|---|
| Start-up, healthy (s) | 1.0, 1.6, 1.1 | **1.2** | 16.3, 10.6, 12.6 | **13.2** |
| First normal request (s) | 16.3, 17.5, 14.7 | **16.1** | 6.3, 3.0, 7.5 | **5.6** |
| Start-up, model broken (s) | 1.7, 2.6, 1.1 | **1.8** | 15.1, 16.1, 10.1 | **13.8** |
| First degraded request (s) | 18.0, 18.9, 13.3 | **16.7** | 0.5, 0.5, 0.5 | **0.5** |
| Second degraded request (s) | 0.4, 0.7, 0.4 | **0.5** | 0.7, 0.4, 0.5 | **0.5** |
| Second normal request (s) | 0.4, 0.8, 0.7 | **0.6** | 2.2, 0.6, 5.9 | **2.9** |
