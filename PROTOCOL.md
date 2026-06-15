# The red-team protocol — `materialize`'s first application

`materialize`'s general capability is a cold, isolated, audited workspace. Its first job is
red-teaming: adversarially validating a claim that some governed decision is **unreachable**
by an attacker who controls a defined surface. First demonstrated on `construct`'s M3 (the
offer-boundary air gap); written to outlive it.

The thesis it serves, in one line:

> A property like "the attacker cannot move this" is only worth believing if a **maximally
> capable** adversary, who knows exactly how the system works, **still cannot** move it.
> A weak attacker's failure proves nothing.

So you hand the attacker every advantage on purpose, and decide the outcome by construction —
not by anyone's testimony, the attacker's least of all.

## The three walls

A red-team on this protocol holds three disciplines. They are the same shape regardless of
what the system-under-test (SUT) is.

### Wall I — capability is declared and bounded, enforced (not requested)

The attacker's power is a **named surface**; everything else is the organ under test. The
bound is not a courtesy — it *is* the experiment. It is enforced two ways:

- **Coldness by construction.** The attacker runs in a workspace that contains *only* the
  declared-readable surface. It cannot read the design discussion because the discussion is
  not in its filesystem — absence, not permission. (`materialize.py`.)
- **A fixture-diff allowlist.** When the attack is a `clean → attacked` pair, the two
  fixtures may differ *only* in fields legal for the declared surface; reaching past it is
  rejected at load. (The SUT supplies this check; construct's is `wall_i_check`.)

### Wall II — the breach is computed from a projection, never narrated

"Did the organ move" is read from a **canonical projection of the system's decision state**,
diffed between a clean baseline and the attacked run. The attacker's account of what it
pulled off is never an input. If it claims a breach the projection does not show, the
verdict is `not_engaged` or `fail` — and that is correct.

- The projection is **pre-decision state only** — exclude downstream consequence (anything
  that legitimately differs *because* the attack changed the outcome), or a "the cost landed"
  result will masquerade as "the organ broke."
- A clean breach is **single-surface**: the only movement is the intended one. A wider
  symmetric difference is `ambiguous`, not a win — tighten the fixture.

### Wall III — the loses/breach cells ship first

Run the attacks designed to *succeed* before claiming the property holds. A breach is a
**finding**, priced and pointed at the missing defense — not an embarrassment. Refusal and
breach are equally first-class results; the harness reports "it held" as readily as "it
moved." A milestone that reported "the organ held" without first running the attacks built
to move it is a victory lap, not a red-team.

## The sealed cold attacker

- **Separated.** Not the system attacking itself — a distinct instance whose objective is to
  win. (Reflexivity collapses the result otherwise.)
- **White-box, framing-cold.** It reads all the *code* (capability), but never the design
  *discussion* or the defenders' *conclusions* (independence). A defense's author shares the
  defense's blind spot; a stranger does not. Prefer a *different model family* from the
  defenders — model diversity is an independence axis.
- **Phased coldness.** Phase A: code + goal only, blind to the spec and the thread — re-derive
  holes, surface unknown-unknowns. Phase B: full spec — confirm the named cells and try to
  **exceed** them. A named cell reproduced is worth little; a breach the named cells miss is
  worth a great deal.
- **Out-of-band at result time too.** It does not post to the design channel. Results reach
  the room as ledgers + a findings doc that a defender presents.

## The pieces

| piece | what it is | reusable? |
|---|---|---|
| `materialize.py` | builds the cold workspace from a phased read-manifest (Wall I coldness) | **yes** — the spine |
| `manifests/<sut>.toml` | the per-SUT coldness boundary, committed + auditable | per-SUT |
| `templates/redteam_brief.template.md` | the ROE; parameterize the SUT-specific bits | **yes** |
| the SUT's runner + projection scorer | clean/attacked pair + the organ-projection diff | per-SUT (construct's `run_m3.py` / `score_redteam.py` is the worked example) |

The SUT contract is thin: expose a way to run on a `clean | attacked` input and emit a
**projection** of the pre-decision state, plus the Wall I allowlist. Everything else —
coldness, the brief, the loses-first discipline — `materialize` supplies.
