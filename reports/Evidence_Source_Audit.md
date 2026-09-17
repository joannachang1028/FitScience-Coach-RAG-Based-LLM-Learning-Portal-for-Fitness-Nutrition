# Evidence Source Audit

Audit date: 2026-09-16

This audit compares the manifest metadata with the content downloaded from each
PMC identifier. It was triggered before gold evaluation labels were created so
that retrieval evaluation would not reward incorrectly labelled evidence.

| Source ID | Result | Note |
|---|---|---|
| `protein_meta_2018` | Pass | Title, corpus content, and DOI align. |
| `acsm_resistance_2026` | Metadata corrected | Corpus content aligns; DOI corrected to `10.1249/MSS.0000000000003897`. |
| `issn_body_comp_2017` | Pass | Title, corpus content, and DOI align. |
| `issn_nutrient_timing_2008` | Pass | Title, corpus content, and DOI align. |
| `neat_review_2018` | Metadata corrected | Corpus content aligns; DOI corrected to `10.20463/jenb.2018.0013`. |
| `micronutrients_review_2015` | Metadata corrected | Corpus content aligns; DOI corrected to `10.2147/OAJSM.S33605`. |
| `energy_balance_2016` | Disabled | PMC5095961 contains an article about severe open Lisfranc fracture treatment, not energy balance. The manifest DOI also refers to an unrelated bat article. |
| `periodization_review_2014` | Disabled | PMC4215195 contains a resistance-exercise volume-load study, not the claimed periodization review. The manifest DOI refers to a soccer article. |
| `supplements_review_2021` | Metadata corrected | Corpus content aligns; DOI corrected to `10.3390/ijerph18178897`. |
| `micronutrient_position_2018` | Pass | Title, corpus content, and DOI align. |

## Required decision

Do not approve gold chunks for `energy_balance_2016` or
`periodization_review_2014` in their current state.

The project owner selected the no-new-source option. Both mismatched records are
disabled and the two evaluation seeds are relabelled against existing sources:

- use `issn_body_comp_2017` for the general relationship between energy balance
  and body composition;
- use `acsm_resistance_2026` for the limited conclusions it contains about
  periodization and resistance-training outcomes.

The alternative is to replace each invalid record with a verified article,
which changes the corpus and requires a fresh ingestion and baseline.
