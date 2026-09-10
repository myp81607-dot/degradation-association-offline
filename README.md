# Degradation Association Offline

Run the rl-insight degradation detector once over a user-selected time range in
the local Prometheus TSDB. The first step value visible after the selected start
is skipped as potentially partial. The next 30 complete steps train a baseline
when no baseline file is supplied; later steps are processed for target events
and grouped Top-25 association evidence.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Analyze a batch

```bash
python -m experiment.degradation.cli analyze \
  --start-time 2026-09-08T09:00:00+08:00 \
  --end-time 2026-09-08T12:00:00+08:00
```

The command reads `~/.rl-insight/data/prometheus` directly with
`promtool tsdb dump`; it does not query the Prometheus HTTP port. Override these
defaults with `--data-dir`, `--promtool`, or `--analysis-dir` when needed.

The command automatically:

- loads an explicitly supplied `--baseline-file`;
- otherwise trains and saves a baseline from the first 30 complete steps;
- analyzes every later complete step;
- runs association once when an event closes, or at the selected range end when
  a confirmed event remains open;
- writes `standard_data.json`, `abnormal_data.json`, and `analysis.json` under
  `analysis/<start>_<end>/` when using the default baseline path;
- prints deterministic evidence for `closed` and `open_at_range_end` events.

The agent uses that evidence to write `report.md`, including the grouped table,
Chinese metric meanings, and root-cause analysis. With `--baseline-file`, the
supplied baseline remains outside the report directory.

Use an existing baseline from another path with `--baseline-file`.

The algorithm retains the online experiment's eight latency targets, 102
candidate metrics, KDE baseline, 3-of-5 event lifecycle, and 0.85 correlation /
0.15 random-forest association weights.

The canonical agent Skill is
`.agent/skills/degradation-association-offline/SKILL.md`. `.claude` and `.codex`
contain symlinks to the same Skill.
