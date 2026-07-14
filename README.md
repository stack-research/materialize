> **ma•te•ri•al•ize**
>
> verb | məˈtirēəˌlīz |
>
> become actual fact; happen: the assumed savings may not materialize.
>- appear or be present: the train didn't materialize.
>
> (of a ghost, spirit, or similar entity) appear in bodily form: he plays a teenager whose make-believe friend materializes.
>- [with object] cause to appear in bodily or physical form: a medium, she was reputed to materialize substances.

---

> A phased read-manifest in, a real **isolated, audited environment** out — with a
> fail-closed provenance record of exactly what's inside. Declarative coldness by
> construction.

The general capability: turn a *declaration* of "what may be present" into a concrete,
standing workspace that contains exactly that and provably nothing else. Its **first job**
was red-team coldness — sealing an attacker away from a system's design discussion so its
blind spots are its own. The **second proven shape is constructive**: a cold *builder* seat
([`construct`](https://github.com/stack-research/construct)'s EFC calibration machinery,
2026-07-12/13) implementing against a sealed spec
inside a workspace that simply does not contain the design discussion, the evidence, or the
facts it must not touch. Same spine, opposite role — the tool is not *about* red-teaming.

Sibling pattern is [`substrate`](https://github.com/stack-research/substrate): a small tool, used in anger immediately, that
becomes infrastructure. The lab's way: prove a capability in one concrete job, then lift it
out as its own thing.

## The spine: `materialize.py`

Given a phased read-manifest and a source repo, build a curated **non-git** sandbox
containing exactly the declared-readable surface — nothing else.

```bash
uv run --no-project python materialize.py \
    --manifest manifests/construct-m3.toml --phase phase_a --dest /tmp/materialize-cm3-a
```

Stdlib only, Python ≥ 3.11 (`tomllib`) — no dependencies to audit in the thing that
guarantees your isolation. A manifest's `source_root` may be relative; it resolves against
the manifest file itself (the committed manifests here expect `construct` checked out as a
sibling of this repo), and `--source` overrides it either way.

- **Whitelist by intent** — only `read` paths are copied (absence by construction).
- **Fail-closed tripwire** — a denylist (`.git`, `.substrate`, `*FINDINGS*`, …) is scanned
  *after* the copy; any hit aborts and removes the workspace. A fat-fingered `read = ["."]`
  cannot silently leak the answer key.
- **Auditable** — `MATERIALIZE_AUDIT.json` in the workspace records exactly what was present
  this phase, with per-file hashes. "Declare your reads," made physical.

## First job: red-team coldness

A claim that *"an attacker cannot move this organ"* is only worth believing if a **maximally
capable** adversary — white-box, optimizing to win — **still cannot** move it. (*Organ* is
construct's vocabulary: a governed decision-making mechanism of the system — the mechanism
itself, not the invariant about it; the invariant under test is that the attacker cannot
move it.) So you hand
the attacker every advantage, and decide the outcome by **construction**, never testimony.

The sharpest "by construction" is the attacker's own **coldness**. A red-team told *"please
don't read the design thread"* is a control enforced by request — the weakness a serious lab
refuses everywhere else. `materialize` enforces it by **absence**: the attacker runs in a
workspace that does not contain the thread, the spec, or the findings, so it cannot read
them. The attacker then operates entirely inside the workspace (`uv run --directory <ws> …`);
it has the SUT's harness and nothing of the SUT's design. Verified for construct M3:

```
workspace top level:  harness/  runs/m3/  REDTEAM_BRIEF.md  MATERIALIZE_AUDIT.json
from the workspace:   .substrate reachable: False   notes reachable: False   SPEC_M3: False
full attack→score loop runs sealed:   AG-channel: pass
```

[`PROTOCOL.md`](PROTOCOL.md) is the project-agnostic red-team protocol that rides on this:
the three walls (declared-and-bounded capability; breach computed from a projection, never
narrated; loses/breach cells ship first) and the sealed cold-attacker discipline.

## Pieces

| path | what | reusable? |
|---|---|---|
| `materialize.py` | the workspace materializer (the spine — the general capability) | **yes** |
| `PROTOCOL.md` | the red-team protocol (first application) | **yes** |
| `templates/redteam_brief.template.md` | the ROE, with the SUT-specific bits parameterized | **yes** |
| `manifests/construct-m3.toml` | consumer #1 — construct M3's red-team coldness boundary, committed + auditable | per-SUT |
| `manifests/construct-efc-calibration-builder.toml` | consumer #2 — construct's cold EFC *builder* seat (constructive shape) | per-SUT |
| `manifests/construct-bootstrap.toml` | probe instance — construct's cold M-1 bootstrap read-surface, made physical | per-SUT |
| `tests/test_materialize.py` | spine smoke (whitelist copy, tripwire abort, audit) | — |

## The SUT contract (thin)

To be red-teamable, a system exposes: a way to run on a `clean | attacked` input and emit a
**projection** of its pre-decision state, plus a Wall I allowlist over the attack surface.
That is all. construct M3's `run_m3.py` (the clean/attacked pair runner) and
`score_redteam.py` (the organ-projection diff) are the worked reference adapter — *not*
vendored here; `materialize` documents the contract and supplies the coldness, the brief, and
the loses-first discipline.

## Status

**v0 — validated on two unlike real jobs.** The spine is built and tested (7/7). Its first
consumer, **construct M3 (adversarial air gap), closed 2026-06-15** — and materialize was the
sealed environment for the whole thing: a cold, off-thread, cross-vendor (Gemini) red-team ran
two phases entirely inside a materialized workspace, blind to the spec in Phase A and to the
design thread throughout, with `MATERIALIZE_AUDIT_PHASE_{A,B}.json` standing as the committed,
hashed record of exactly what each phase could read. Coldness held **by construction** (verified
from inside the workspace: `.substrate`, `notes`, the spec all unreachable), and the attack→audit
loop caught a milestone-inverting bug a reviewer had accepted — which is the dividend of sealing
the attacker away from the defenders' conclusions. The construct-M3 instance lives at
`manifests/construct-m3.toml`.

**Second validated job — the constructive shape (2026-07-12/13).** Construct's EFC
calibration-machinery **builder** ran three implementation/correction/closure rounds as a
cold seat inside one standing materialized workspace
(`manifests/construct-efc-calibration-builder.toml`): sealed spec + accepted design +
implementation source present; the substrate design threads, findings, run evidence,
corpora, and fixture facts **absent by construction** (a per-manifest `forbidden` list
extends the built-in tripwire). The audit round-tripped byte-identical across all three
rounds, 272 tests passed inside the workspace, and two independent cold auditors passed the
result A–G — with the builder's received-context *declaration* backed by
`MATERIALIZE_AUDIT.json` per-file hashes instead of testimony. The role inverted (builder,
not attacker) and the spine didn't care: that inversion is what earns the *general* name.
One naming wrinkle carried honestly: the brief still lands in the workspace as
`REDTEAM_BRIEF.md` even for a builder — a rename (`BRIEF.md`) is future work, not done
quietly here.

Consumers: **construct M3** (✅ red-team — validated), **construct EFC builder**
(✅ constructive — validated), **substrate's red-team** (planned). A third instance,
`construct-bootstrap.toml`, materializes the M-1 cold-bootstrap read surface as a probe.
Deliberately **not coupled** into any SUT: their runners stay standalone until materialize
stabilizes across consumers — prove in one job, then lift out.

## License

MIT — see [LICENSE](LICENSE).
