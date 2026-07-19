# Data Card: DOB Complaint Universe

Generated 2026-07-11 from the official bulk export of *DOB Complaints Received* (NYC Open Data `eabe-havv`). Raw data stays local; this card and its JSON summary are aggregates with a source checksum for exact reproducibility.

- **Total complaints:** 3,106,954
- **First / last complaint date:** 1988-12-30 → 2026-07-11
- **Rows with an inspection date:** 99.7%
- **Source:** 347,372,384 bytes, SHA-256 `18a109b9bdf50a5b…`

## Complaints per year

| Year | Complaints |
| --- | ---: |
| 1988 | 1 |
| 1989 | 22,523 |
| 1990 | 23,317 |
| 1991 | 23,342 |
| 1992 | 21,184 |
| 1993 | 21,361 |
| 1994 | 20,005 |
| 1995 | 21,956 |
| 1996 | 26,571 |
| 1997 | 33,064 |
| 1998 | 35,558 |
| 1999 | 36,593 |
| 2000 | 43,520 |
| 2001 | 45,122 |
| 2002 | 51,990 |
| 2003 | 62,539 |
| 2004 | 78,209 |
| 2005 | 108,875 |
| 2006 | 112,954 |
| 2007 | 129,246 |
| 2008 | 142,982 |
| 2009 | 127,198 |
| 2010 | 113,511 |
| 2011 | 103,796 |
| 2012 | 100,305 |
| 2013 | 95,216 |
| 2014 | 101,591 |
| 2015 | 101,823 |
| 2016 | 114,454 |
| 2017 | 126,256 |
| 2018 | 128,846 |
| 2019 | 135,472 |
| 2020 | 112,548 |
| 2021 | 119,129 |
| 2022 | 121,448 |
| 2023 | 131,449 |
| 2024 | 125,148 |
| 2025 | 119,471 |
| 2026 | 68,381 |

## Top complaint categories (raw codes)

| Category code | Count | Share |
| --- | ---: | ---: |
| 45 | 423,823 | 13.64% |
| 05 | 416,118 | 13.39% |
| 63 | 148,165 | 4.77% |
| 73 | 124,241 | 4.00% |
| 30 | 93,267 | 3.00% |
| 31 | 83,845 | 2.70% |
| 04 | 83,065 | 2.67% |
| 59 | 82,416 | 2.65% |
| 83 | 78,996 | 2.54% |
| 6S | 67,370 | 2.17% |
| 23 | 60,806 | 1.96% |
| 55 | 57,218 | 1.84% |
| 37 | 54,087 | 1.74% |
| 58 | 53,583 | 1.72% |
| 4B | 52,167 | 1.68% |

## Status

| Status | Count | Share |
| --- | ---: | ---: |
| CLOSED | 3,086,558 | 99.34% |
| ACTIVE | 20,396 | 0.66% |

## Why this exists

The current AHV cohort (782 complaints, ~16 actionable outcomes) cannot support the Sprint 3 predictive tier on its own. This profile scopes the cohort-widening decision across the full complaint universe: which categories carry enough volume and enough disposition variation to give temporal validation a real positive class.

Category, unit, and disposition codes are profiled as raw codes on purpose: mapping them to labels and outcome semantics is the documented Sprint 3 modeling decision, not a profiling step. Counts are complaint-level; one building can generate many complaints, so building-level dedup happens downstream.
