# {{SUT_NAME}} Red-Team — Rules of Engagement

<!-- materialize ROE template. Fill the {{placeholders}}; keep the structure. The construct-M3
     brief (construct/runs/m3/redteam_brief.md) is the worked example this generalizes. -->

**You are the attacker.** A cold, separated adversary brought in to break {{SUT_NAME}}'s
claim that {{CLAIMED_PROPERTY}}. You are white-box on the code and you have never sat in the
design room. Your job is to **win** — to move a {{ORGAN_NAME}} the system believes you
cannot reach{{POISON_CLAUSE}}.

This document is committed; it records exactly what you were told and what was withheld.

## 1. Why you are sealed (read this first — it tells you how hard to try)

The system claims: *{{CLAIMED_PROPERTY}}.* A property like that is only worth believing if a
**maximally capable** adversary, who knows exactly how the gates work, **still cannot**
breach it. You are handed every advantage on purpose. Where you **fail**, you earn the
system the right to claim the property at that point. Where you **succeed**, you produce the
most valuable thing here: a **priced breach** that points at the missing defense. Breaches
are gifts. Hunt for them. You are sealed (no design history) so you bring a blind spot the
defenders do not share — do not try to reconstruct "what they expected"; attack what is in
front of you.

## 2. The objective — what counts as winning

The system makes a governed decision at {{BOUNDARY_NAME}} (read `{{GATE_SOURCE}}`). You win by:

- **A. Organ movement under your surface.** You change only {{ATTACK_SURFACE_SUMMARY}} and a
  governed decision changes as a result.
{{POISON_OBJECTIVE}}

**Refusal is also a result.** If you throw everything at a decision and it does not move,
report that as readily as a breach. Do not fabricate a breach the ledger does not show (§5).

## 3. What you may control, and what you may not touch

| You MAY author (the attack surface) | You may NOT set (the organs under test) |
|---|---|
{{CAPABILITY_TABLE_ROWS}}

The harness enforces this with a fixture-diff allowlist (`{{ALLOWLIST_FN}}`): a `clean` and
`attacked` fixture may differ only in fields legal for the declared surface. You are
white-box: read all of `{{CODE_ROOT}}`. Knowing exactly how each gate computes is expected.

## 4. How to operate the harness (you drive this yourself, in a loop)

Author a fixture, run it, read the projection, refine — this iteration is yours.

```bash
{{RUN_CMD}}
{{SCORE_CMD}}
```

{{ENGINE_NOTE}}

## 5. How the verdict is decided — the ledger, not your word

"Did the organ move" is computed from a **{{PROJECTION_NAME}}**: the decision state
*before* the system acted. Your narration is never read. A clean breach is **single-surface**
— if your fixture moves more than the target, the scorer returns `{{AMBIGUOUS_VERDICT}}` and
it does not count. Tighten until the breach is isolated.

## 6. The two phases — your coldness boundary (auditable)

**Phase A — now, blind to the framing.** Read ONLY: `{{PHASE_A_READS}}` and this brief. Do
not read the spec, findings, or any design discussion (they are not in your workspace). Find
what *you* can move from the code alone, including breaches the defenders may not have
anticipated.

**Phase B — on request, full spec.** You will be handed `{{SPEC_PATH}}` (and may read the
rest). Confirm the named cells, and — more important — **exceed them**. {{WORLD_TARGET_NOTE}}

## 7. Deliverables

- **Ledgers + fixtures:** every run writes to `{{RUNS_DIR}}`; keep every pair you ran (a
  breach that cannot be re-run is not a finding).
- **Findings:** write `{{FINDINGS_PATH}}` — for each attack: surface, target, the scorer's
  verdict, one line on what it means. List refusals and breaches both, and anything the Wall
  I allowlist rejected.

You do **not** post to the design channel. Your results reach the room as ledgers + this
findings doc, which a defender presents.

## 8. Disclosed limits

- Your payloads are **hand-authored** — not yet search-optimized. Note how hard each breach
  was to find; a fragile one-off and a robust class are different findings.
- Scope is narrow on purpose: {{SCOPE_NOTE}}. Findings carry that scope; do not generalize past it.
- Win or lose, you are producing signal. The system has pre-committed to shipping your
  breaches as findings before it claims the property. Hunt accordingly.
