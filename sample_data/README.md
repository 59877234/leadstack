# Sample data provenance

`propstream_skiptraced.csv` — all column headers verified against real
PropStream export code (see CLAUDE.md). Row values are synthetic test data.

`propstream_marketing.csv` — `Owner 1 First/Last Name` and `Mailing
Address/City/State/Zip` are verified real PropStream headers. The
`Property Address/City/State/Zip` columns are **not verified** for
PropStream's marketing-list export specifically — that column name wasn't
in any source I could confirm. They're included here only to exercise the
cross-file dedup logic end to end; treat them as a placeholder until
checked against a real PropStream marketing export.
