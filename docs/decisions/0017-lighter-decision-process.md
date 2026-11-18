# 0017. Lighter decision process: the owner's ok replaces the teach-back
- Status: Accepted. Supersedes the decision process and research rule 1 of
  [0001](0001-conventions.md).
- Date: 2026-11-18. Decided by: owner (Eudes Fileti), proposed by the agent. Process:
  infrastructure. Carried over from hidrotopia-co2, where it is ADR-0017 (2026-11-16); the
  number is kept so that "ADR-0017" means the same rule in every repo.

## Context
ADR-0001 asked for a teach-back (the owner's own words, checked by the agent) on every
research or methodology decision. In hidrotopia-co2 it kept ADRs open and blocked the
experiment doc, at a cost in the owner's time larger than the risk the decisions carried.
The safeguard that protects the results is cheap and needs no teach-back: the analysis
method is written down before the production data are analysed. New projects start from
this template, so the template carries the same process.

## Decision
1. No teach-back. The agent proposes each decision in 2–3 lines (what and why); the owner
   answers "ok" or "approved"; the record keeps that answer and the agent's justification.
2. An ADR only for general choices about physics, simulation protocol, analysis method or
   repo infrastructure. Experiment-specific choices (systems, run length, reading rules)
   go in the experiment doc; small choices go in the journal entry (Decisions).
3. The research rules of ADR-0001 stay, as rules the agent applies. Rule 1 is split:
   - Descriptive result (a value ± error per system): before the production data are
     analysed, the experiment doc fixes the quantity, the analysis parameters (e.g.
     discarded initial time, averaging window, block length) and how the error is computed.
   - Comparative result (A differs from B; a trend across systems or conditions): also
     fixes beforehand when a difference counts (e.g. larger than k × the combined error, k
     fixed beforehand); outcomes yes, no or inconclusive.
   - The rule is never changed after the results are seen; a changed rule makes a new claim.
   Rule 2 (a number is stated only from a claim built on registered results) is unchanged.
   Rule 3 (fair comparisons) also reads, for MD and AIMD: same force field or level of
   theory, protocol and length for every system compared, and the same analysis
   parameters, fixed before the results are seen.
4. ADR-0001 becomes Accepted with these changes.
5. Numbering: 0013–0016 are not used in the template (project ADRs of hidrotopia-co2).
   Projects number their own ADRs from 0101, so a later template ADR never takes a number
   a project already uses.

## Owner's approval and agent's check
- Owner, 2026-11-16 (hidrotopia-co2): "olha, eu acho que estamos fazendo um overkill com
  essa coisa de teach-back e ADR. As decisoes sao muito obvias e ter que ficar explicando e
  respondendo parece ser perda de tempo." Then "aprovado." to that proposal.
- Owner, 2026-11-18: "ok." to carrying ADR-0017 and the acceptance of ADR-0001 into the
  template; "ok." to the numbering (point 5).
- Agent's justification: keeps the one safeguard that protects the results (method fixed
  before the data are seen, same analysis for every system) and drops the step that cost
  the owner time without adding protection.

## Consequences
- Experiment docs and claims are no longer blocked in projects created from the template.
- hidrotopia-co2 keeps its own ADR-0017 (same rule, project-specific consequences).
- Projects created before this ADR keep their ADR numbers; only new projects use 0101+.
