# Data sources

## the-2027-top50.csv

| Column | Meaning | Source |
|---|---|---|
| `rank` | Position in the table. `=` means tied | THE World University Rankings 2027 |
| `university` | University name (some shortened, e.g. "LMU Munich", "EPFL") | THE World University Rankings 2027 |
| `city`, `country`, `country_code` | Main campus location | University websites |
| `region` | Americas, Europe, Asia or Oceania, used for colours | Derived from country |
| `overall_score` | THE overall score out of 100 | THE World University Rankings 2027 |
| `best_for` | Short summary of the fields each university is best known for | Author's summary, not a THE ranking |

- Official table: https://www.timeshighereducation.com/world-university-rankings/latest/world-ranking
- Published: 30 September 2026
- Checked: 21 October 2026, against THE's regional tables and launch coverage

Ranking data © Times Higher Education. Reproduced with credit for information and commentary.

## edition-2027.json

Edition settings: year, data file, byline, the takeaway cards on the last page and the source line. The takeaway facts were checked against the CSV and THE's 2027 launch highlights.
