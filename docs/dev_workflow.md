# Development Workflow Specification
Version: v1.0  
Language: English  
Audience: Developer + GPT

---

## 1. Purpose

This document defines the **development workflow** for the scanner project.  
It ensures:

- consistent development across GPT sessions
- clean versioning
- reproducible migrations
- controlled spec→code evolution
- minimized context loss
- traceability between spec/config/snapshots

The workflow is designed to support a **GPT-assisted development style** with incremental refactoring.

---

## 2. Core Principles

The workflow follows these principles:

1. **Spec → Code → Snapshot → Backtest**
2. **Version everything**
3. **Track structural changes explicitly**
4. **Never overwrite context**
5. **Prefer additive iteration over rewrite**
6. **Preserve determinism**

---

## 3. Components Managed by Workflow

The workflow coordinates:

- `spec.md` (master technical spec)
- `/docs/*.md` (modular specs)
- `config.yml` (runtime parameters)
- `code_map.md` (structural overview of codebase)
- `README.md` (user/system guide)
- `gpt_snapshot.md` (context handoff between GPT sessions)
- snapshots (runtime data)
- backtest results (evaluation outputs)

---

## 4. Workflow Cycle (Core Loop)

Development cycle:

```
(1) Update Spec (if needed)
(2) Update Config (if needed)
(3) Implement Code
(4) Update Code-Map
(5) Update README
(6) Run Scanner
(7) Produce Snapshot(s)
(8) Optional Backtest
(9) Review / Adjust / Iterate
```

This loop is future-proof and compatible with research workflows.

---

## 5. Code-Map Integration

Whenever code changes structurally, developer/GPT must:

- update `code_map.md`
- reflect modules, functions, ownership, naming, interfaces

Code-map becomes the single source of truth for **repository structure**.

---

## 6. README Integration

README must explain:

- what the scanner does
- how to run it
- how to install dependencies
- how to schedule
- how to update config
- how to interpret outputs

README must not contain low-level architecture (that belongs to docs).

---

## 7. GPT-Snapshot Integration

GPT-Snapshot captures:

- recent changes
- context diffs
- open questions
- unresolved tasks
- constraints
- warnings/notes
- migration hints

Snapshot is fed into next GPT session to continue without context loss.

---

## 8. Version Control

Version control requirements:

- spec version
- config version
- code version
- snapshot version

Version increments on:

- scoring logic changes
- feature schema changes
- mapping rules changes
- pipeline changes
- config parameter changes

---

## 9. Development Modes

Workflow supports:

| Mode | Purpose |
|---|---|
| research | tune scoring + features |
| implementation | coding work |
| refactor | structural changes |
| debug | fix issues |
| backtest | evaluate setups |
| freeze | prepare release |

Modes allow GPT to adjust reasoning style.

---

## 10. Snapshot Discipline

Snapshots must be:

- immutable
- timestamped
- version-stamped
- backtest-compatible

No retroactive mutation.

---

## 11. Backtest Discipline

Backtest outputs must not overwrite:

- config
- spec
- code-map

Backtest informs, but does not mutate.

---

## 12. Migration Discipline

When spec changes materially:

1. increment spec version
2. adjust config if required
3. migrate code if required
4. regenerate snapshots if relevant
5. evaluate via backtest

This prevents “silent drift”.

---

## 13. GPT Collaboration Rules

GPT must:

- read spec before implementing
- read code_map before refactoring
- use snapshot for context recovery
- ask before structural rewriting
- never mutate spec without prompt
- never delete context

These rules prevent runaway architectural mutations.

---

## 14. Deliverables & Outputs

Workflow produces:

- code
- docs
- snapshots
- reports
- backtests

Artifacts must be consumable by human and machine.

---

## 15. Anti-Goals

The workflow must not:

- embed speculation into code
- optimize prematurely
- discard context
- silently refactor
- collapse setup types into one
- make hidden model changes

---

## 16. Extensible Workflow

Future modules may include:

- CLI tools
- execution modules
- dashboard
- metrics
- alerts
- parameter search

Workflow supports extension without rewrite.

---


## 17. CI & Dependency Discipline

CI must install dependencies explicitly from versioned requirement files:

- runtime deps: `requirements.txt`
- test/dev deps: `requirements-dev.txt` (includes `pytest`)

No implicit dependency on preinstalled runner packages is allowed.

---

## 18. Bot/Quota Outage Fallback Process

If live provider calls fail due to quota/outage:

1. Use cache only if a valid cache exists.
2. Mark output metadata as degraded and include freshness timestamps.
3. If no cache exists, fail fast with explicit error (do not emit unlabeled partial data).
4. Document incident handling in PR notes if behavior changed.

---

## End of `dev_workflow.md`
