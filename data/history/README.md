# Run history

One Playwright JSON report per run, named in run order:

```
run-001.json
run-002.json
run-003.json
```

After a run, copy the reporter's output here as the next number:

```sh
cp results.json data/history/run-002.json
```

`get_test_history` reads every `run-*.json` in this directory. It is
configured as `HISTORY_DIR` in `.mcp.json`; a relative path there is read
from the project root, so pointing it elsewhere takes one line.

## What is in here now

Five runs, committed so the history tools work on a fresh clone.

`run-001.json` is a real report. `run-002` through `run-005` are generated from
it (2026-08-27 to 2026-09-08) so there is something to compare: the same 15
test/project pairs in every run, with outcomes that differ between runs -- a
failure that gets fixed, one that never does, one that only fails on firefox,
and a few that flake and pass on retry.

Replace them with your own runs, or point `HISTORY_DIR` at a directory of them.
