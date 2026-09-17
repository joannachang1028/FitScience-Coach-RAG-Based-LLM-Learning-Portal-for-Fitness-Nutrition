# Evaluation Gold Candidate Review

Review status: **approved by project owner on 2026-09-16**

The proposed labels, now promoted to `data/evaluation_gold_seeds.jsonl`, were selected by
reading the source sections directly, not by accepting the current retriever's
top-ranked passages. The validator checks that every proposed chunk exists and
belongs to an expected source, but it cannot decide whether the scientific
interpretation is correct.

## Candidate summary

| Seed | Proposed source | Gold chunks | Main interpretation to review |
|---|---|---:|---|
| `protein_target` | Protein meta-analysis | 3 | Small average benefit; plateau estimate near 1.6 g/kg/day is uncertain, not a universal prescription. |
| `protein_ceiling` | Protein meta-analysis | 2 | No further average FFM gain above the estimated breakpoint; not an individual hard ceiling. |
| `protein_timing` | 2008 ISSN position stand | 3 | Timing may support glycogen, protein synthesis, recovery, and adaptation; label must disclose source age and avoid universal prescription. |
| `resistance_frequency` | 2026 ACSM overview | 2 | Healthy adults: high-effort RT at least twice weekly, all major muscle groups. |
| `progression` | 2026 ACSM overview | 3 | Increase stimulus through several variables; not required for initial benefit but relevant to continued progress. |
| `body_composition` | 2017 ISSN position stand | 2 | Sustained deficit drives fat loss; surplus supports lean-mass gain; several diet patterns can work. |
| `neat` | NEAT review | 3 | Definition, examples, variability, contribution to TEE, and limits of obesity association. |
| `micronutrients` | Athlete-nutrition review | 3 | Individual needs, limited ergogenic supplements, diet quality, contamination and anti-doping risk. |
| `energy_balance` | 2017 ISSN position stand | 3 | Deficit/surplus affect body composition, but expenditure adapts and individual responses vary. |
| `periodization` | 2026 ACSM overview | 2 | No consistent aggregate outcome advantage; this does not mean periodization is always useless. |
| `supplements` | 2021 supplement review | 4 | Need, evidence, excess intake, duplication, adulteration, interaction, and oversight. |
| `micronutrient_supplement` | Academy position paper | 3 | Use when requirements are unmet or deficiency is diagnosed; assessment is required. |

## Human decisions required

For each candidate, confirm:

1. The selected chunks directly support the reference answer.
2. The required claims are necessary but not overly specific.
3. The disallowed claims capture unsafe or unsupported extrapolation.
4. The answer is appropriate for an educational assistant rather than a
   diagnostic or prescriptive system.

## Resolved conflict

The seed `creatine_missing` remains labelled `insufficient_evidence`, although
`issn_nutrient_timing_2008::c004` contains a creatine dose claim. The question
asks, “What dose of creatine should I take?”, which is personalized and the
source is an older position stand. The project owner decided that this does not
support a current individualized recommendation. The expected response may
describe that limitation but must not turn the historical dose into personal
advice.
