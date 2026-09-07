# Offline Degradation Algorithm Contract

## Workflow

```text
Prometheus matrix JSON/TXT
  -> merge concrete labeled series
  -> align samples to global-step intervals
  -> load a frozen baseline or train it from the first 30 complete steps
  -> classify later steps and track target events
  -> calculate correlation/random-forest association at confirmed and closed
  -> save event JSON and present grouped Top-25 evidence
```

## Input and alignment

- Require exactly one concrete
  `rl_insight_monitor_training_global_step` series.
- Define step `k` as `[timestamp(k), timestamp(k + 1))` and use the last finite
  sample in that interval.
- Preserve missing metric values and distinct label sets.
- Require consecutive global-step boundaries; never infer a missing step.
- Merge repeated input files by concrete series and timestamp.

## Metric roles

The eight scalar `UP` event targets are:

1. `rl_insight_monitor_timing_s_step`
2. `rl_insight_monitor_timing_s_gen`
3. `rl_insight_monitor_timing_s_ref`
4. `rl_insight_monitor_timing_s_adv`
5. `rl_insight_monitor_timing_s_old_log_prob`
6. `rl_insight_monitor_timing_s_update_actor`
7. `rl_insight_monitor_timing_s_update_weights`
8. `rl_insight_monitor_timing_s_testing`

The 102 configured scalar candidates use a `BOTH` policy and are grouped as
`latency`, `training_quality`, `rollout_quality`, `data_characteristics`,
`hardware_resources`, `vllm_engine`, and `transfer_queue`. Candidate anomalies
support association but never trigger target events.

## Baseline and detection

- Train a Gaussian KDE baseline from the first 30 complete steps when no
  baseline file exists; require at least 20 finite samples per fitted series.
- Load an existing schema-compatible `standard_data.json` without retraining.
- Require at least one fitted target and one fitted candidate.
- Confirm a target when at least three of five consecutive valid target points
  are above its fitted normal range.
- Close the active event when a later complete five-point window has fewer than
  three abnormal points.
- Missing target points delay lifecycle transitions.

## Association

- Analyze once at confirmation and again at closure.
- Retain 30 steps of pre-event context.
- Require at least 10 aligned target/candidate points for correlation.
- Random forest requires at least 30 common samples and both normal/abnormal
  classes in its chronological 70/30 train/validation split.
- Combine normalized evidence with correlation weight `0.85` and random-forest
  weight `0.15`; use the only valid evidence path at full effective weight.
- Return at most 25 candidates for each phase.
- Treat association score only as relative evidence within that event window.

## Output

`standard_data.json` stores fitted baseline ranges, not the raw first 30 steps.
`abnormal_data.json` stores confirmed/closed events and flat deterministic
Top-25 records. CLI stdout presents the same records grouped by metric category
for model interpretation.
