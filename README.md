# MCP Response Guard

> Runtime schema validation and drift detection for MCP server responses.
> Detect when MCP tool outputs deviate from their declared JSON schemas.

## The Problem

MCP (Model Context Protocol) servers declare tool schemas — but their actual outputs often drift:
- **Schema violations**: Server returns fields not in schema, misses required fields, or wrong types.
- **Silent failures**: Agent receives malformed data and hallucinates corrections.
- **No runtime checks**: Existing tools (`mcp-validators`, `mcptools`) validate schema *definitions*, not live *responses*.
- **No drift detection**: No tool compares responses across calls to detect when a server's output shape changes.

## The Solution

`mcp-response-guard` sits between your agent and MCP servers, validating every response against declared schemas and tracking drift over time.

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

## Features

- **Runtime validation** — Every MCP response validated against declared JSON schema.
- **Drift detection** — Track schema violations over time; alert when drift exceeds threshold.
- **SARIF output** — GitHub Code Scanning compatible reports.
- **CI gate** — Fail CI if drift detected in integration tests.
- **Multi-server** — Guard multiple MCP servers from a single process.
- **Non-blocking mode** — Log violations without breaking agent workflows.

## Install

```bash
pip install git+https://github.com/yunaremaia/mcp-response-guard.git
```

## Quick Start

```python
from mcp_response_guard import Guard

guard = Guard()
guard.add_server("filesystem", "http://localhost:3000/mcp")

# Agent calls tool — response is auto-validated
result = guard.call("filesystem", "read_file", {"path": "/etc/hosts"})

# Check drift report
report = guard.drift_report()
print(f"Violations: {report.total_violations}")
```

Or as middleware:

```bash
# Wrap any MCP client
mcp-guard -- mcp-client --server filesystem
```

## What It Detects

| Code | Level | Description |
|------|-------|-------------|
| MCPR001 | HIGH | Response missing required schema field |
| MCPR002 | HIGH | Response has extra field not in schema |
| MCPR003 | MEDIUM | Response field type mismatch |
| MCPR004 | LOW | Response shape drift from historical baseline |
| MCPR005 | MEDIUM | Server error response not matching error schema |

## Drift Detection

Unlike static schema checkers, `mcp-response-guard` maintains a baseline of observed responses per tool. When the shape changes (new fields, removed fields, type changes), it flags drift even if the response is technically valid.

```bash
# Generate drift report
mcp-response-guard report --since 7d --format json

# Fail CI on drift
mcp-response-guard check --drift-threshold 0.1
```

## Comparison

| Tool | Validates Responses | Drift Detection | Runtime | SARIF |
|------|---------------------|-----------------|---------|-------|
| **mcp-response-guard** | ✅ | ✅ | ✅ | ✅ |
| mcp-validators | Schema definitions only | ❌ | Build-time | ❌ |
| mcptools | No | ❌ | CLI | ❌ |
| MCP Guard (yunaremaia) | Schema definitions only | ❌ | Build-time | ✅ |

## Roadmap

- [ ] Baseline auto-learning (first N calls establish baseline)
- [ ] Slack/email alerts on drift
- [ ] Integration with `agent-undo` for rollback on violation
- [ ] OpenTelemetry spans for violation tracing

## License

MIT
