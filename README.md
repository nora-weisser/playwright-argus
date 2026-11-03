# Playwright Argus

An MCP server that lets an LLM agent read Playwright test reports. A Playwright
JSON report is tens of thousands of lines and mostly noise; these tools answer
the questions you would otherwise scroll for — what failed, which failures share
a cause, and whether a test has been failing for weeks or only started today.

```
> which tests are the least reliable?

  rate  test                                       last     pattern
  1.00  checkout.spec.ts > TC-C02: order summary    failed   locator-ambiguous
  1.00  dashboard.spec.ts > TC-D01: loads widgets   failed   timing-or-waiting
  0.80  cart.spec.ts > TC-R01: persists the cart    flaky    assertion-failure
```

## Features

| Tool | Answers |
|---|---|
| `get_test_summary` | How the latest run went: counts, duration, plus `errors` for anything that failed outside a test (a global setup that threw). Such a run reports zero of everything else, so `errors` is the only sign it did not succeed. |
| `get_failures` | The failed tests, with `test_id`, `file`, `project`, `status` and the fullest error message. Flaky tests included; `status` tells them apart. |
| `get_failure_patterns` | Those failures grouped by what their errors look like — `locator-not-found`, `assertion-failure`, `network-failure` — biggest group first. |
| `get_unstable_tests` | The tests that fail or flake most often across past runs, worst first. Where an investigation starts, since every other history question needs a `test_id`. |
| `get_test_history` | One test, run by run: how often it failed, how it failed each time, and whether it is still failing. |

Two details worth knowing: a test running on two browsers produces two results
per run, so `total_runs` and `total_results` are counted separately and rates
are out of the latter. And `instability_rate` counts flakes alongside failures,
because a test that only ever passes on a retry is not a healthy test.

## Prerequisites

- Python ≥ 3.10
- [uv](https://docs.astral.sh/uv/) — `brew install uv`, or `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Node.js, only for `mcp dev` (the MCP Inspector)

## Install

```bash
uv sync
```

That is the whole setup. A sample report and five runs of history are bundled in
`data/`, so every tool answers immediately — no configuration, and no Playwright
project needed to try it.

## Use it

### With Claude Code

The repository ships a project-scoped `.mcp.json`, so there is nothing to write:

```bash
claude          # from the repository root, then approve the server when prompted
```

Check it with `/mcp` in the session, or `claude mcp list` in a terminal, then
ask: *"which tests are the least reliable?"*

Servers load at startup, so restart the session if it was already running. To
register it globally instead, pass `--directory` so `uv` finds this project's
venv from anywhere:

```bash
claude mcp add playwright-argus -s user -- \
  uv --directory /absolute/path/to/playwright-argus run playwright-argus
```

### With Claude Desktop

Add to `claude_desktop_config.json` (`~/Library/Application Support/Claude/` on
macOS), then quit with Cmd-Q and reopen:

```json
{
  "mcpServers": {
    "playwright-argus": {
      "command": "uv",
      "args": ["--directory", "/absolute/path/to/playwright-argus",
               "run", "playwright-argus"]
    }
  }
}
```

Logs land in `~/Library/Logs/Claude/mcp-server-playwright-argus.log`.

### By hand

```bash
uv run mcp dev src/playwright_argus/server.py   # Inspector, in a browser
uv run playwright-argus                         # plain stdio server
```

## Point it at your own project

Generate a report with the `json` reporter:

```bash
npx playwright test --reporter=json > results.json
```

Then set two variables — `REPORT_PATH` for the latest run, `HISTORY_DIR` for a
directory of past ones named `run-001.json`, `run-002.json`, … Both default into
`data/`, both are re-read on every call, and relative paths resolve from the
repository root rather than the working directory.

Build history by copying each run in as the next number; anything matching
`run-*.json` is read. Three runs is where a trend starts to mean anything.

```bash
cp results.json data/history/run-006.json
```

Where you set the two variables depends on how the server was started:

| Launched by | Configuration comes from |
|---|---|
| Claude Code / Desktop | the `env` block in the client's JSON config |
| Your shell (`mcp run`, `playwright-argus`) | exported variables |
| MCP Inspector (`mcp dev`) | the Inspector's own Environment Variables fields |

The Inspector is the odd one out: it spawns servers with a fixed set of
variables (`HOME`, `LOGNAME`, `PATH`, `SHELL`, `TERM`, `USER`) and drops
everything else, so exporting `REPORT_PATH` before `mcp dev` has no effect.

## Tests

```bash
uv run pytest
```

58 tests, no mocking — every one reads a real report through the real parser.

| File | | Covers |
|---|---|---|
| `test_playwright_report.py` | 20 | Parsing one report: stats, failure fields, flaky tests, ANSI stripping, pattern grouping, and the messages given for a missing, truncated or non-Playwright file |
| `test_history.py` | 26 | Aggregating many reports: counts and rates, run-vs-result counting, the instability ranking and its tie-breaks, ordering, empty and unknown cases |
| `test_server_tools.py` | 7 | The MCP contract — each tool listed, called over an in-memory client, returning the expected shape |
| `test_config.py` | 5 | Path resolution: relative vs absolute, defaults, explicit overrides |

Fixtures in `tests/fixtures/` hold the reports they read, including a run with
flaky tests and a run that died in global setup. Tests needing exact rates build
their runs in a `tmp_path` instead.

## How the code is laid out

```
src/playwright_argus/
  server.py              the five MCP tools, and nothing else
  config.py              where REPORT_PATH and HISTORY_DIR resolve to
  playwright_report.py   the one place that knows Playwright's JSON shape
  models/                the normalized shapes every analysis starts from
  analysis/              failure classification, history, instability ranking
  history/loader.py      reads the stored runs, reusing playwright_report.py
data/
  results.json           sample report: the latest run
  history/run-00N.json   five past runs, for the history tools
```

A stored run and the latest run go through the same parser, so the history tools
and the latest-run tools cannot disagree about what a test is.

## Troubleshooting

| Symptom | Cause |
|---|---|
| Tools answer about the wrong tests | `REPORT_PATH` is unset, so the server is reading the bundled sample |
| `No Playwright report at ...` | The path in the message is what `REPORT_PATH` resolved to; relative paths come from the repository root |
| `... is not a Playwright JSON report` | Not `json`-reporter output — an HTML report, or a blob |
| `ModuleNotFoundError: playwright_argus` | A client ran `uv` without `--directory` from outside the repository |
| Server missing from `/mcp` | Servers load at startup: restart the session, and approve the project-scoped server |
| `mcp dev` will not start | Node.js is missing, so there is no `npx`; use `mcp run` instead |

Avoid `uv run mcp install …`: it registers the server with `--with mcp[cli]` in
an isolated environment and no `--directory`, so this package is never
importable.

## License

MIT — see [LICENSE](LICENSE).
