# MCP Response Guard

> Runtime schema validation and drift detection for MCP server responses.
> Detect when MCP tool outputs deviate from their declared JSON schemas.

## Status: proposal, not released

**This repository contains no implementation.** It is a design proposal: a
README, a license and nothing else — no `src/`, no `pyproject.toml`, no CLI, no
tests, no CI. There is nothing to install and no `mcp_response_guard` module to
import today.

Everything below is a *proposal*, written out far enough to be reviewed and
argued with. The feature list, the API sketch, the detector codes and the
comparison table are all aspirational. Treat them as a spec, not as
documentation of shipped behaviour.

Real, working tools in this space:

- [`mcp-guard`](https://github.com/yunaremaia/mcp-guard) — validates MCP server
  configurations and tool schemas at build/CI time, with SARIF output.
- [`vibeguard`](https://github.com/yunaremaia/vibeguard) — audits agent
  configuration for prompt-injection and secret exposure, with SARIF output.

## The Problem

MCP (Model Context Protocol) servers declare tool schemas — but their actual outputs often drift:

- **Schema violations**: Server returns fields not in schema, misses required fields, or wrong types.
- **Silent failures**: Agent receives malformed data and hallucinates corrections.
- **No runtime checks**: Existing tools (`mcp-validators`, `mcptools`) validate schema *definitions*, not live *responses*.
- **No drift detection**: No tool compares responses across calls to detect when a server's output shape changes.

## Proposed Solution

`mcp-response-guard` would sit between your agent and MCP servers, validating every response against declared schemas and tracking drift over time.

```
┌──────────┐    ┌──────────────────┐    ┌──────────────┐
│  Agent   │───▶│  Response Guard  │───▶│  MCP Server  │
│          │◀───│  (validate+log)  │◀───│              │
└──────────┘    └──────────────────┘    └──────────────┘
                        │
                        ▼
                ┌───────────────┐
                │  Drift Log    │
                │  (SQLite)     │
                └───────────────┘
```

## Proposed Features

None of these exist yet.

- **Runtime validation** — validate every MCP response against its declared JSON schema.
- **Drift detection** — track schema violations over time; alert when drift exceeds a threshold.
- **SARIF output** — GitHub Code Scanning compatible reports.
- **CI gate** — fail CI if drift is detected in integration tests.
- **Multi-server** — guard multiple MCP servers from a single process.
- **Non-blocking mode** — log violations without breaking agent workflows.

## Proposed API

```python
# Not implemented. Sketch of the intended interface.
from mcp_response_guard import Guard

guard = Guard()
guard.add_server("filesystem", "http://localhost:3000/mcp")

result = guard.call("filesystem", "read_file", {"path": "/etc/hosts"})

report = guard.drift_report()
print(f"Violations: {report.total_violations}")
```

Intended CLI surface:

```bash
# Not implemented.
mcp-response-guard report --since 7d --format json
mcp-response-guard check --drift-threshold 0.1
```

## Proposed Detector Codes

| Code | Level | Description |
|------|-------|-------------|
| MCPR001 | HIGH | Response missing required schema field |
| MCPR002 | HIGH | Response has extra field not in schema |
| MCPR003 | MEDIUM | Response field type mismatch |
| MCPR004 | LOW | Response shape drift from historical baseline |
| MCPR005 | MEDIUM | Server error response not matching error schema |

## Proposed Drift Detection

Unlike static schema checkers, the design would maintain a baseline of observed responses per tool. When the shape changes (new fields, removed fields, type changes), it would flag drift even if the response is technically valid.

## Landscape

| Tool | Validates Responses | Drift Detection | Runtime | SARIF |
|------|---------------------|-----------------|---------|-------|
| **mcp-response-guard** | proposed | proposed | proposed | proposed |
| mcp-guard | Schema definitions only | No | Build-time | Yes |
| vibeguard | No | No | Build-time | Yes |
| mcp-validators | Schema definitions only | No | Build-time | No |
| mcptools | No | No | CLI | No |

## Roadmap

- [ ] Implement the core guard and publish a first release
- [ ] Baseline auto-learning (first N calls establish baseline)
- [ ] Slack/email alerts on drift
- [ ] Integration with `agent-undo` for rollback on violation
- [ ] OpenTelemetry spans for violation tracing

## License

MIT
