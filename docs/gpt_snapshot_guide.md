# GPT Snapshot Guide
Version: v1.0  
Language: English  
Audience: Developer + GPT

---

## 1. Purpose

The GPT Snapshot is a **context handoff artifact** that allows development to continue across separate GPT sessions **without context loss**.

It acts as a compact, structured, high-signal memory for:

- current status
- unresolved tasks
- pending decisions
- spec diffusion
- implementation progress
- warnings & caveats
- migration notes

Snapshots make GPT collaboration **stateful**, even though GPT itself has no persistent memory.

---

## 2. Why Snapshots Matter

GPT-assisted development naturally suffers from:

- statelessness between chats
- partial context retention
- hallucinated architectural rewrites
- lost TODOs
- forgotten design constraints
- out-of-sync code/spec

The GPT Snapshot prevents these failure modes.

---

## 3. What a Snapshot Is (and Is Not)

A snapshot **is**:

- a concise project-state capsule
- a structured summary
- a coordination mechanism
- a lightweight context diff

A snapshot is **not**:

- a spec
- a changelog
- a README
- code
- a Code Map
- a transcript of discussion

Its job is continuity, not documentation.

---

## 4. Snapshot Timing

Snapshot entries should be created:

- at the end of work sessions
- before handing over to a new GPT session
- after architectural or scoring changes
- before migrations
- after backtests or evaluation insights
- before freezing a milestone

Rule of thumb:
> “If context would be lost without explanation → snapshot it.”

---

## 5. Snapshot Format (v1)

Recommended block structure:

```
GPT Snapshot (YYYY-MM-DD)

Status
  high-level current state

Recent Changes
  structural / spec / config / code changes
  snapshot-level granularity

Open Tasks
  prioritized TODOs
  next actions

Pending Decisions
  places requiring confirmation
  forks in architecture or scoring

Warnings / Caveats
  known risks, instabilities, ambiguities

Notes to Future GPT
  instructions, constraints, etiquette
  tips for continuing without context loss
```

Small, readable, deterministic.

---

## 6. Examples of Good vs Bad Snapshots

**Good:**

```
Status: Current branch goal and completion level.
Open tasks: explicit TODO list with owners/priority.
Decision pending: unresolved threshold/logic decisions.
Warnings: known risks and reproducibility caveats.
```

**Bad:**

```
We talked about stuff, need to fix things.
```

---

## 7. Snapshot Storage Location

Snapshots should be stored at:

```
/snapshots/gpt/
```

File naming convention:

```
gpt_snapshot_YYYY-MM-DD.md
```

This ensures chronological lineage.

---

## 8. Snapshot + Spec Interaction

Snapshots must not mutate the spec.  
Snapshots may request spec changes.

Workflow:

```
snapshot -> discussion -> spec update -> code update
```

Spec is authoritative; snapshot is ephemeral.

---

## 9. Snapshot + Code Map Interaction

Snapshots record structural changes, but Code Map encodes them.

Process:

```
snapshot records change
developer/GPT implements
code_map updates to reflect repo
```

---

## 10. Collaboration Protocol for GPT

GPT must:

1. read latest snapshot before coding
2. read spec before structural changes
3. read code_map before refactoring
4. not overwrite snapshot unless asked
5. not erase prior context
6. ask clarification if snapshot ambiguous

These rules reduce architectural drift.

---

## 11. Anti-Goals

Snapshot must not:

- be verbose
- contain implementation detail
- hide open questions
- repeat spec
- be formatted as prose

It is not a diary.

---

## 12. Extensibility

Future snapshots could store:

- performance metrics
- backtest summaries
- tuning deltas
- parameter diffs

v1 focuses only on context continuity.

---

## 13. Summary

The GPT Snapshot is:

- small
- structured
- contextual
- actionable

It enables persistent momentum across iterations and sessions.

---

## End of `gpt_snapshot_guide.md`
