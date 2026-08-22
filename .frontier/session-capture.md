# Frontier Session Capture — Specification v1

This is the canonical, vendor-neutral definition of how an agent produces a session trace.

Claude, Codex, or any other assistant implements a thin adapter that reads this file and follows it.
No vendor-specific file may redefine the contract; adapters exist only to bridge a particular tool's
invocation mechanism to this specification.

Machine-readable contract: `.frontier/schema/session-v1.schema.json`.

---

## 1. Purpose

Frontier repositories accumulate two kinds of history. Git records what the code became.
Session traces record **how the engineer's understanding got there** — what was attempted, what broke,
what was believed beforehand, what evidence changed that belief, and what remains unknown.

The long-term intent is a machine-readable corpus describing how these repositories, the hardware,
and the engineer's capability evolve. That corpus may later inform courses, construction guides,
exercises, assessments, troubleshooting material, and tutoring.

None of that is built yet, and v1 must not anticipate it. The immediate job is to capture good raw
material in a format that survives.

A trace is **source capture, not teaching material.** A session trace never contains a lesson,
a tutorial, or an exercise write-up. It records that such material could be built, and from what.

## 2. When to create a trace

Traces are created **only when the user explicitly asks**, at the end of a session. Never automatically,
never on exit, never as a background process.

Capture a session when real engineering understanding moved. For example:

- understanding an ELF, linker, or toolchain behaviour;
- bringing up a peripheral for the first time;
- diagnosing an interrupt, clock, or timing problem;
- implementing and debugging a bus such as SPI, I2C, or CAN;
- analysing a logic-analyser or oscilloscope capture;
- first power-on of a custom PCB;
- an architecture or toolchain decision with lasting consequences;
- a failure that took real effort to understand, even if unresolved.

Do not capture:

- typo and formatting fixes;
- editor navigation or trivial shell usage;
- routine dependency bumps;
- a session where nothing was learned, tried, or decided.

A session that produced no code but genuinely changed a mental model **is worth capturing**.
A session that produced a lot of code but taught nothing usually is not.

Use judgement. One good trace is worth more than five dutiful ones.

## 3. Inspect repository state before writing

Conversational recollection is the weakest evidence available. Before writing a trace, observe the
repository directly. At minimum:

```sh
git rev-parse --show-toplevel
git rev-parse --abbrev-ref HEAD
git rev-parse HEAD
git status --short
git log --oneline -n 10
```

Record what these report, not what you remember. Where the session's claims touch files, re-read the
files rather than trusting the conversation. Where the session ran commands, quote them as they were
actually run — including the ones that failed.

If the working tree is dirty, say so in `repository.dirty`. A trace written against uncommitted work is
still useful, but the reader must know the referenced state was not yet permanent.

Tool versions belong in `repository.toolchain`, and only when relevant to the session. This is not an
inventory; a linker session records the linker's version, not the whole machine.

### Capture after committing

Make the session's code and documentation commits first, then capture. The order is not cosmetic.

`persistence: committed` means "tracked in this repository at the recorded commit, recoverable exactly."
Capture with a dirty tree and that claim is false for the session's own files: they must be downgraded to
`ephemeral`, discarding the strongest evidence class available. `repository.head_commit` has the same
problem — captured early it names the state *before* the work, and `commits_created` is empty, so the trace
describes something nothing it references can reach.

The sequence:

1. Commit the session's code and documentation changes.
2. Capture. The trace records the real HEAD and the real commit SHAs.
3. **Read the trace.** This is the gate that matters — after commit it is historical, and corrections
   require a superseding trace.
4. Commit the trace on its own.

The trace therefore lands one commit after the work it describes. That is correct: it describes that commit,
so it cannot precede it. Do not contort the workflow to get the trace and the code into a single commit —
the durable link is the SHA recorded inside the trace, which survives rebases, cherry-picks, and file moves.
Co-location in one commit does not.

Two caveats:

- **This must not become a reason to skip capture.** A session that produced no commits is still worth
  capturing — exploratory work, reading primary documentation, an unresolved bring-up failure. Leave
  `commits_created` empty, record `dirty: true` honestly, and mark evidence `reproducible` or `ephemeral`
  as it actually is. The rule is to prefer committed evidence, not to refuse uncommitted work.
- **Never commit code you would not otherwise commit** just to improve a trace's evidence. The work drives
  the commits; the trace records them.

## 4. Distinguish evidence from recollection

Every load-bearing statement in a trace falls into one of four categories, recorded in `claims[].status`:

| Status | Meaning |
|---|---|
| `observed` | Seen directly: tool output, a measurement, or text in a primary document. |
| `inferred` | Reasoned from observations. Sound, but a step removed. |
| `hypothesis` | Plausible, untested. Explicitly not yet knowledge. |
| `unresolved` | Contested, unknown, or awaiting evidence. |

The purpose of this field is narrow and important: **an agent's confident explanation is not evidence.**
Without this distinction, a fluent-sounding guess made during a session becomes indistinguishable from a
measured fact six months later, and the corpus quietly poisons itself.

Anything not `observed` **must** carry `verification_required` — what would actually settle it.
This is enforced by the schema and by the validator, not left to good intentions. A claim you cannot say
how to verify is usually a claim that should not be recorded as knowledge at all.

Where a primary document supports a claim, cite it precisely in the evidence registry: document ID,
revision, and location (e.g. page number). "The datasheet says so" is not a citation.

## 5. Capture the learning progression

This is what separates a session trace from a conversation summary. A summary records what the agent
said. A trace records **what the engineer believed, what they saw, and what they believe now.**

Use `learning.model_updates` for this, and keep all three parts:

```json
{
  "topic": "Linker MEMORY regions",
  "prior_model": "A region declaration is enough to make code land at that address.",
  "prior_model_provenance": "explicit",
  "observation": "Map file showed .text at 0x08010010 despite FLASH originating at 0x08000000.",
  "updated_model": "MEMORY declares available address ranges; SECTIONS decides placement. Unnamed sections are orphans placed by linker heuristics.",
  "confidence": "high",
  "still_uncertain": "Whether lld and GNU ld order orphans identically."
}
```

Rules that matter:

- **Keep `prior_model` even when it was wrong.** Especially when it was wrong. The incorrect belief is
  the most pedagogically valuable field in the entire schema — it is what a future learner will also believe.
- **`prior_model_provenance` is mandatory and must be honest.** `explicit` means the learner actually said
  it — quote or closely paraphrase. `inferred` means you deduced it from what was asked or attempted.
  When in doubt, it is `inferred`.

  This distinction guards a specific and severe failure mode: an agent inventing a plausible-sounding
  misconception and recording it as something the learner believed. Mined across hundreds of traces,
  fabricated beliefs would produce confident conclusions about learning difficulties that no human ever had.
  Only `explicit` entries are empirical evidence of what someone believed; `inferred` entries are the trace
  author's reading and must be treated as such downstream.

  Note what the field does and does not do. It is a labelling convention supporting human review and later
  filtering. It cannot *prevent* fabrication — an agent willing to invent a belief can mislabel it just as
  easily. It works only to the extent that the agent is honest, and that the human reviewing the trace
  checks the `explicit` entries against what they actually remember saying.
- Do not record a model update that did not happen. A session where the user already understood something
  and had it confirmed is an `observation`, not an update.

`learning.concepts[].exposure` deliberately offers no value meaning "mastered". The strongest available
value is `verified_by_experiment`, meaning the learner predicted a result and then observed it. An agent
explaining a concept clearly produces `explained` and nothing more. Resist inflating this field; a corpus
that overstates competence is worse than no corpus.

Record misconceptions in `learning.misconceptions`, including the agent's own. `held_by` accepts `agent`
for good reason — assistants state things wrongly, and a corrected agent error is real signal about where
this material is genuinely confusing.

`misconceptions[].provenance` carries the same `explicit` / `inferred` requirement as `prior_model`, for the
same reason and with the same limits. A misconception nobody voiced, recorded as `explicit`, is the most
corrupting single entry that can enter this corpus.

### Fields that grade themselves

Several fields record the trace author's own assessment rather than an observation. Each is enforced to
require the thing that would substantiate it:

| Assertion | Must also supply |
|---|---|
| `claims[].status` is not `observed` | `verification_required` |
| `concepts[].exposure` is `verified_by_experiment` | `evidence` |
| `failures[].resolved` is `true` | `resolution` |
| `misconceptions[].corrected` is `true` | `correction` |
| `experiments[].status` is `completed` | `observed_result` |

These are cheap to satisfy honestly and awkward to satisfy dishonestly, which is the point. If supplying the
second column is difficult, that is usually the signal that the first column is overstated — downgrade the
assertion rather than inventing support for it.

One deliberate omission: a `completed` experiment is **not** required to carry `predicted_result`. Demanding
a prediction after the outcome is known invites one reconstructed to match, which is worse than an absent
field. Record the prediction when it was genuinely made beforehand, and leave it out otherwise.

## 6. Preserve failures and unresolved questions

Failures are first-class records, not embarrassments to be tidied away by the time the trace is written.

For each failure worth recording, keep:

- the failure **as it presented**, quoting the actual error text where possible;
- the hypotheses considered, **including those that turned out to be wrong**, each marked
  `rejected` / `supported` / `untested` with a reason;
- the diagnostic steps in the order taken;
- the root cause, if it is genuinely known;
- the resolution, and whether it is `resolved` at all.

A hypothesis that was pursued and abandoned is not noise. It is a map of the wrong turns available at
that junction, and it is exactly what makes later troubleshooting material realistic.

`pedagogical_value` is optional and should stay empty unless the answer is genuine. Manufactured
significance is worse than a blank field.

Unresolved questions go in `learning.unresolved_questions` with `why_it_matters` and `blocked_on`.
A trace that ends with open questions is a good trace. Do not manufacture closure.

## 7. Record future ideas without doing course work

Ideas that arise naturally during engineering — "this failure would make a great exercise", "you'd need
to understand X before Y makes sense" — belong in `future_work`.

The boundary is firm: **capture the pointer, not the material.**

- Correct: `{"exercise": "Break the link by declaring only MEMORY, then have the learner locate the misplaced section in the map file", "verification": "learner identifies the 0x10000 alignment jump unaided"}`
- Wrong: writing the exercise, its solution, or its explanatory preamble into the trace.

If capturing future work starts to feel like authoring curriculum, stop. The session was engineering work;
the trace is its record. Course design happens later, elsewhere, by a different process reading many traces.

`future_work.prerequisites` deserves particular attention because it is hard to reconstruct later. When
you notice during a session that one idea genuinely had to land before another made sense, record it while
the ordering is still obvious.

## 8. Evidence references

All artifacts referenced by the trace are declared once in the top-level `evidence` array and referenced
elsewhere by `id`. This keeps a single auditable list and avoids repeating paths.

Rules:

- **Reference, never embed.** No file contents, no capture data, no long log dumps inside the trace.
  A short quoted error line is fine; a pasted build log is not.
- Prefer **repository-relative paths** (`linker/stm32f030r8.ld`, `build/fm001.map`).
- For artifacts outside the repository, use a **descriptive reference**: document ID and revision, a
  board identifier, a capture filename with where it lives.
- Absolute machine-specific paths age badly. Avoid them unless nothing else identifies the artifact.
- Note that build outputs are frequently gitignored. Referencing `build/fm001.map` is still correct —
  it identifies what was examined — but the file itself may not be recoverable later. Where a build
  artifact carries the key evidence, quote the decisive lines in the relevant `observation` so the finding
  survives the file's deletion.
- `location` carries the position within an artifact: `"page 39/775"`, `"line 25"`, `"channel 2, 4.2 ms"`.

Every evidence item declares `persistence`, because a reference is only as useful as the reader's ability to
follow it later:

| Value | Meaning |
|---|---|
| `committed` | Tracked in this repository at the recorded commit. Recoverable exactly. |
| `reproducible` | Not stored, but regenerable by re-running a recorded command against a recorded commit. |
| `ephemeral` | Neither stored nor reliably regenerable — a gitignored build output, console scrollback. |
| `external` | Outside the repository — a vendor datasheet, a capture file on a lab machine. |

**When evidence is `ephemeral`, the decisive content must also be quoted into an `observation`.** This is the
rule that keeps a trace meaningful after `build/` is cleaned. A trace whose central finding rests only on a
path that no longer exists has recorded nothing. The validator warns when a `committed` item points at a path
that looks like build output.

This deliberately does not create an artifact store. If particular captures later justify archival — logic
analyser sessions, oscilloscope datasets, manufacturing measurements — that is a considered decision for a
future version, not something to start doing by default.

Identifiers live in separate namespaces per record type — `evidence`, `failures`, `experiments`, `claims` —
and must be unique within their own. References are resolved **by field name, not by value**: an `evidence`
array resolves only against evidence ids, `failure_id` only against failure ids. A reference that names a
real id of the wrong kind is an error, not a coincidence the validator will accept. Prefix ids to keep this
readable in review (`ev-`, `fail-`, `exp-`, `claim-`).

Hardware identity is evidence. Board and PCB revisions belong in `hardware`, because the same firmware
behaves differently across revisions and a trace without that context can mislead badly later.

Record the **class and revision** of hardware, not the individual unit. The schema has no field for serial
numbers, probe IDs, or MCU unique device IDs, deliberately: traces are committed and may be shared, and such
values identify a specific machine or person while almost never explaining an engineering result. If a
per-unit identifier genuinely matters — a fault reproducible on exactly one board — describe it in `notes`
use `hardware[].unit_alias`: a project-local name such as `board-a` or `fm-motor-a03`. Being a real field
rather than prose, it supports correlating one unit across many traces — which is the actual engineering
need — without recording an MCU UID, a probe serial, or a manufacturer identifier. The alias is a name the
project assigns and controls; keep it stable once chosen, and record the mapping outside the corpus if you
need one.

The evidence registry is subject to the same policy. It has no `hardware_id` type, and a `ref` or command
string must not become the back door through which a serial arrives — record
`openocd -c "hla_serial <elided>"` rather than the real value.

## 9. Naming, storage, and immutability

Traces are stored in `.frontier/sessions/` as JSON, one file per session:

```text
.frontier/sessions/YYYY-MM-DDTHHMMSSZ-short-topic.json
```

- **The timestamp is UTC and the trailing `Z` is mandatory.** Filenames written in different timezones must
  still sort chronologically against one another; a local-time basis breaks that silently and cannot be
  repaired once traces accumulate. `created_at` inside the file may carry a real local offset — that is
  where timezone information belongs.
- `short-topic` is lowercase kebab-case, a few words, describing the subject: `linker-flash-overflow`.
- `trace_id` inside the file **must equal the filename without `.json`**.
- Lexicographic sort equals chronological sort. This is deliberate; keep it.

Synthetic example traces live in `.frontier/examples/`, are prefixed `EXAMPLE-`, and set `"example": true`.
They must never be placed in `sessions/`, which is reserved for real engineering history.

**Immutability.** Once a trace is committed, it is a historical record. Do not silently edit it to reflect
later understanding — the fact that something was believed on a particular day is itself the data.

- Before commit: edit freely.
- After commit: write a **new trace** that records the correction and lists the original in `supersedes`.
- Typographical fixes that change no meaning are acceptable in place.
- A superseded trace is never deleted.

This matters because the corpus is meant to show how understanding *changed*. Rewriting history to look
correct destroys precisely the signal that makes the corpus worth keeping.

## 10. Validation

Validate before reporting completion:

```sh
python3 .frontier/validate.py .frontier/sessions/<trace>.json
```

The validator uses the `jsonschema` package when it is installed and otherwise falls back to a
dependency-free structural check covering required fields, types, enums, and patterns. It additionally
performs checks JSON Schema cannot express:

- every referenced id exists **in the namespace the referencing field implies**;
- ids are unique within each namespace;
- an evidence item claiming `persistence: committed` does not point at something that looks like build output;
- `trace_id` matches the filename;
- traces in `sessions/` are not marked `example`.

The fallback is deliberately imperfect. It supports the keywords this schema actually uses, including
`allOf` and `if`/`then` so the cross-field rules above are honoured without `jsonschema` installed. Note that
timestamps are constrained by `pattern` rather than by `format`: JSON Schema treats `format` as an annotation
by default, so a `format`-only constraint would be enforced by neither path.

Its limitation is silence rather than noise — if a future schema uses a keyword the fallback does not
implement, the fallback ignores that keyword and reports `ok`. Any schema change must therefore be
parity-tested against both paths before it lands. If validation ever needs to be authoritative — in CI, say —
install `jsonschema` in the project environment and use the real path. Do not grow the fallback further
into a JSON Schema implementation.

## 11. Writing style for traces

Deliberately boring. These are records, not prose.

- Plain declarative statements. No narrative voice, no enthusiasm, no summarising flourish.
- Quote real text — error messages, command lines, document wording — rather than paraphrasing it.
- Prefer many short structured entries over few long ones.
- Empty is better than padded. An absent array means "nothing here", which is honest and useful.
  A fabricated entry corrupts the corpus permanently.
- Assume the reader is a stranger, possibly a program, possibly years later, with none of the session's
  context and no access to the conversation.

## 12. Relationship to other project files

This repository already keeps `.agent/` files (`status.md`, `decisions.md`, `discoveries.md`,
`open-questions.md`). They serve a different purpose and both should continue:

| | `.agent/` | `.frontier/sessions/` |
|---|---|---|
| Shape | Current-state summary | Append-only historical record |
| Edited | Continuously, in place | Written once, superseded not rewritten |
| Answers | "Where does the project stand?" | "How did understanding get here?" |
| Audience | The next session | A future corpus, and humans reviewing progress |

Overlap in content is expected and fine. A verified finding may reasonably appear in both
`.agent/discoveries.md` and a session trace. They are not competing sources; one is a live summary,
the other is a dated record with its evidence attached.

Session capture does not replace, and must not silently modify, the `.agent/` workflow.
