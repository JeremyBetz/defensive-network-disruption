# Project charter

Status: exploratory foundation, 2026-09-09. Public documentation reviewed; no
competition data files accessed or empirical construct, estimand, or result established.

## Context and problem

This is a USA-region Football entry for PySport Analytics Cup 2.0. The supplied
challenge is Defensive Positioning using permitted SkillCorner Australia
A-League 2024/25 data. The supplied judging priorities are sporting relevance,
sound methodology, originality, clear communication, and reusable open-source
work. Competition constraints and their source status live in
[competition_rules.md](competition_rules.md).

An analyst can observe a tackle, but defensive positioning may also matter
before a ball action occurs. The football problem is whether the positioning
of defenders can be related to the suppression of available attacking options
in an interpretable and testable way. This is a hypothesis, not an established
source of defensive value.

## First scientific objective

Determine whether a meaningful, continuous attacking-connection measure can be
defined from the permitted data such that defender positioning measurably and
interpretably attenuates those connections. The initial question is:

> At a given moment, what does it mean for two attacking players to have a viable
> connection, and how can defender positioning continuously weaken it?

The candidate observable is a directed connection strength `w_ij(t)`. Its
semantics, units, scale, support, time horizon, and validation target are all
undecided. A current ball-carrier-to-receiver connection and a hypothetical
connection between two off-ball attackers are different constructs. Success on
the former would not establish validity of the latter. The estimand must be
specified prospectively before outcome evaluation.

## Two spatial networks

The attacking layer would represent players and defensible potential
connections. The defensive layer would represent support, cover, spacing, or
other explicitly defined structural relationships. Defender positions may
interact with attacking connections while a defender's movement also changes
their own team's structure. This motivates a dynamic, spatially embedded,
adversarial multiplex framing; it does not require a particular graph algorithm.

The long-term question is how much attacking possibility a configuration might
remove for how much structural compromise. A disruption-minus-deformation
formula is conceptual scaffolding only. There is no assumed common scale,
exchange rate, additive decomposition, or utility function between these
quantities. Topology comes after measurement, and structural cost is a separate
validation problem.

## Intended use and originality

The desired first practitioner output is an understandable explanation of
which candidate receiving options a configuration appears to make accessible
or difficult, with uncertainty and failure cases. Later outputs might help a
coach examine stepping out, cover, or multiple-option suppression. Recruitment
rankings and individual value estimates require much stronger evidence.

The separate `moving-the-defense` project studies associations between
off-ball attacking movement and localized defensive reorganization. This project
instead begins with the measurement of attacking connections under defensive
positioning and may later study the tradeoff with defensive support. Neither
the old outcome nor its estimates, findings, tuned parameters, figures, data, or
validation set is an input to this project. Its public README was reviewed at
the user's request; published summaries were visible, but no code or results
were imported. Prior match exposure must be audited before choosing holdouts.

The submission must contain substantial new work created specifically for Cup
2.0. General technical lessons, coding patterns, and geometric reasoning may
inform design; any actual later reuse must pass the provenance and eligibility
review in [research_governance.md](research_governance.md). Reuse must not become
a lightly adapted prior study.

## Scope, unknowns, and non-claims

Unknowns include dataset access and permitted release, cross-product match
overlap, coordinate and time conventions, ball/possession reliability, tracking
quality and missingness, event semantics and synchronization, pose coverage,
feasible reference outcomes, sampling units, and viable validation partitions.
All proposed dataset counts are expectations from the brief, not audit results.

No claim is made that:

- a visible passing lane is a viable pass or a completed pass proves accessibility;
- edge strength is a calibrated probability or can represent unchosen options;
- geometric occlusion measures a cover shadow, perception, or player intent;
- movement direction is body orientation, or two pose games generalize;
- weaker connectivity benefits the defense or predicts a worse attacking outcome;
- defender effects are independent, additive, causal, or individually identifiable;
- structural preservation is equivalent to compactness or necessarily desirable;
- any resulting score measures player quality or defensive value.

## Open-source objective and completion standard

Original code and documentation use MIT licensing. Competition data is local
and separately governed. The eventual method should be reusable from Python
without proprietary software, but this scaffold promises no public model API.
Only a validated construct should motivate interfaces for connections,
attenuation, topology, or structure.

Early success can be a well-supported negative result or a clearly bounded
measurement. Initialization is complete when the research gates, data boundary,
claim ledger, importable empty modules, and no-data checks are in place; it is
not evidence of scientific success.
