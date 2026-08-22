# `.frontier/`

Frontier-owned, vendor-neutral engineering-learning capture.

Git records what the code became. This directory records **how understanding got there**: what was
attempted, what broke, what was believed beforehand, what evidence changed that belief, and what is
still unknown.

## Layout

```text
.frontier/
├── README.md                      this file
├── session-capture.md             canonical specification — the contract agents follow
├── schema/
│   └── session-v1.schema.json     machine-readable trace format
├── sessions/                      real session traces, append-only history
├── examples/                      synthetic traces demonstrating the format
└── validate.py                    dependency-optional validator
```

## Using it

At the end of a session where something was genuinely learned, ask the agent to capture it. With Claude
Code that is `/session-capture`; other tools bridge to the same specification through their own mechanism.

Then check the result:

```sh
python3 .frontier/validate.py                    # all traces
python3 .frontier/validate.py path/to/trace.json  # one trace
```

Traces are meant to be read by a human before being committed. The agent wrote them from a conversation;
you are the one who knows whether they are true.

## Design principles

**Frontier owns the contract.** `session-capture.md` and the schema are vendor-neutral. Claude, Codex, or
anything else supplies only a thin adapter that reads the specification and follows it. Vendor names appear
inside traces as data (`agents[].provider`), never as structure. If a vendor file ever contradicts the
specification, the specification wins.

**Evidence outranks recollection.** Repository state, command output, measurements, and primary documents
are stronger than what anyone remembers a conversation saying. Traces record where each claim sits on that
scale, because a fluent explanation from an agent is not a fact.

**Learning progression, not conversation summary.** The valuable record is `prior model → observation →
updated model`, retained even when — especially when — the prior model was wrong.

**Failures are kept.** Rejected hypotheses and wrong turns are not tidied away. They are the map of the
mistakes actually available at that junction.

**Committed traces are historical.** Corrections are made by writing a new trace that lists the original in
`supersedes`, not by rewriting the old one. That a thing was believed on a given day is itself the data.

**Source capture only.** A trace may note that a failure would make a good exercise. It never contains the
exercise. Course material, if it is ever built, is a separate process reading many traces.

## Relationship to `.agent/`

Both continue; they answer different questions.

| | `.agent/` | `.frontier/sessions/` |
|---|---|---|
| Shape | Current-state summary | Append-only historical record |
| Edited | Continuously, in place | Written once, superseded not rewritten |
| Answers | "Where does the project stand?" | "How did understanding get here?" |
| Audience | The next session | A future corpus, and humans reviewing progress |

Overlapping content is expected. A verified finding may sit in both `.agent/discoveries.md` and a trace.

## Deliberately not here

No database, vector store, knowledge graph, embeddings, RAG, telemetry, background agents, automatic
transcript ingestion, course generation, dashboards, or cloud services.

v1 is plain JSON files in Git. Those things get added if and when an accumulated corpus demonstrates the
need — not in anticipation of it.
