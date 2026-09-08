---
name: degradation-association-offline
description: "Analyze saved Prometheus JSON/TXT batches for RL training latency degradation, grouped Top-25 associations, and concise root-cause hypotheses. Use for offline data, not live monitoring."
---

# Offline degradation association

Use the deterministic code in `experiment/degradation`. Do not reimplement or
change its KDE baseline, eight default targets, 3-of-5 event lifecycle,
association ranking, or metric categories.

Read [algorithm-contract.md](references/algorithm-contract.md) before running the
analysis. Read [diagnostic-experience.md](references/diagnostic-experience.md)
only when at least one confirmed or closed event contains association entries.

## 1. Environment check

Locate the checkout containing `experiment/degradation/cli.py` and run commands
from its repository root. If imports are missing, report them and ask before
running `pip install -e .`.

Use `outputs/degradation-association-offline` as the default state directory
unless the user supplies another path. The files are:

```text
<state-dir>/standard_data.json   # fitted or loaded baseline
<state-dir>/abnormal_data.json   # events and association evidence
```

## 2. Offline data input

Accept one or more Prometheus matrix files or directories. Both `.json` and
`.txt` extensions are accepted when their contents are valid JSON. Merge all
files by metric name, complete label set, and timestamp. Preserve labels and
use `rl_insight_monitor_training_global_step` as the step ruler.

Keep all discovered configured metrics. Never restrict input to trainer metrics
or discard non-trainer candidates. Exactly the eight `timing_s_*` metrics in the
algorithm contract are event targets; the other configured scalar metrics are
candidate evidence.

If a text export is not valid JSON, inspect its actual structure. Write a small
temporary converter only when needed, producing Prometheus matrix entries with
`metric` and `values: [[timestamp, value], ...]`. Do not invent timestamps,
values, metric names, or labels, and do not collapse differently labeled series.

## 3. One-shot anomaly and association analysis

Run the complete batch once:

```bash
python -m experiment.degradation.cli analyze <file-or-directory> [...] \
  --state-dir outputs/degradation-association-offline
```

If `standard_data.json` exists, the command loads it and analyzes complete input
steps after that baseline's `end_step`. Otherwise it trains the baseline from
the first 30 complete steps, saves it, and analyzes every remaining complete
step. A separately supplied baseline may be selected with `--baseline-file`.

Wait for the command to finish. Do not stop after baseline training and do not
split a batch into repeated monitor calls. The one command performs point
detection, confirmed/closed event tracking, and Top-25 association analysis.

For every event phase with association entries, present the complete returned
Top-25, or all entries when fewer are available. Group by English metric
category in best-score order, then sort metrics within each group by descending
score. Keep every category in one contiguous block. Write the category name only
in the first row of that block and leave the category cell blank in its
remaining rows, even when the category contributes many Top-25 metrics. Do not
repeat the category name and do not insert separator rows or horizontal rules
between metrics or category blocks. Show only these columns:

| Metric category | Metric name | Association score |
|---|---|---:|
| transfer_queue | tq_partition_consumption_progress | 94.80% |
|  | tq_storage_utilization_ratio | 91.25% |
|  | tq_storage_request_latency_p99 | 89.10% |
| latency | rl_insight_monitor_perf_throughput | 88.60% |
|  | rl_insight_monitor_perf_time_per_step | 84.30% |

Precede the table with:

```text
Abnormal target metric: <target>
Event phase: <confirmed|closed>
Saved result: <absolute abnormal_data.json path>
```

Association score is relative evidence, not fault probability or causality. If
there are no events, state that the batch produced no abnormal target event. If
an event phase has no association entries, report its stored status and do not
invent a diagnosis.

## 4. Root-cause analysis

For each event phase with evidence, use the target, phase, metric names,
categories, global ranks, final `association_percent` values, and the experience
reference. Use only the returned final association scores for evidence strength.
Do not reopen raw series, write another analysis script, compare step values, or
independently infer increases, decreases, trends, or change magnitude.

Do not use candidate direction, point state (`NORMAL`, `UP`, `DOWN`, or
`BETWEEN_MODES`), matched mode, or candidate abnormality as a diagnosis gate.
Combine association ranking with metric semantics and technical knowledge. When
length or sequence metrics occupy a substantial part of the returned Top-K,
`Sequence-length anomaly` MUST appear among the likely causes. When they also
form the leading high-scoring evidence group, it MUST be cause 1. Apply this rule
regardless of candidate direction or point state; do not infer whether sequence
length increased or decreased. Many weak scores alone do not justify high
confidence. This length-family rule is the explicit exception to the general
rule that category size alone is not a vote. The experience reference remains a
fallible prior.

Use the fault domains `Compute`, `Network`, `Host CPU`, and `HBM`. Rank exactly
two distinct domains and three to five plausible causes in confidence order.
Low confidence is acceptable. Keep the reasoning concise and do not claim
unobserved hardware, network, profiler, or operating-system signals.
`Sequence-length anomaly` is a workload/data condition rather than one of the
four fault domains. When the sequence-length rule applies, the two fault domains
are only infrastructure alternatives and must not displace that diagnosis; keep
them low-confidence unless stronger non-length association evidence exists.

```text
Primary fault domain: <domain> (confidence: High|Medium|Low)
Secondary fault domain: <domain> (confidence: High|Medium|Low) — <brief basis>

Likely fault causes:
1. <cause> (primary; confidence: High|Medium|Low) — <brief basis>
2. <cause> (confidence: High|Medium|Low) — <brief basis>
3. <cause> (confidence: High|Medium|Low) — <brief basis>
[4-5 when supported]

Reasoning basis: <two or three concise professional sentences>
```

This Skill analyzes supplied observations only. Do not provide fault-injection
commands or procedures.
