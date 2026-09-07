# Degradation Association Offline

Run the rl-insight degradation detector once over saved Prometheus matrix data.
The first 30 complete global steps train a baseline when no baseline file exists;
the remaining steps are processed for target events and grouped Top-25
association evidence.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Analyze a batch

```bash
python -m experiment.degradation.cli analyze data/ \
  --state-dir outputs/degradation-association-offline
```

Inputs may be individual `.json`/`.txt` files or directories. File contents
must be valid JSON containing Prometheus `query_range` matrix results. Multiple
files are merged by metric name, labels, and timestamp.

The command automatically:

- loads `standard_data.json` from the state directory when present;
- otherwise trains and saves it from the first 30 complete steps;
- analyzes every later complete step;
- writes deterministic event records to `abnormal_data.json`;
- prints grouped association evidence for every confirmed and closed event.

Use an existing baseline from another path with `--baseline-file` and choose a
different result path with `--output`.

## Accepted matrix shape

```json
{
  "status": "success",
  "data": {
    "resultType": "matrix",
    "result": [
      {
        "metric": {
          "__name__": "rl_insight_monitor_training_global_step",
          "job": "training"
        },
        "values": [[1000, "0"], [1010, "1"]]
      }
    ]
  }
}
```

The algorithm retains the online experiment's eight latency targets, 102
candidate metrics, KDE baseline, 3-of-5 event lifecycle, and 0.85 correlation /
0.15 random-forest association weights.

The canonical agent Skill is
`.agent/skills/degradation-association-offline/SKILL.md`. `.claude` and `.codex`
contain symlinks to the same Skill.
