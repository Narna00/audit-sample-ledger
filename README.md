# Audit Sample Ledger

Produce repeatable stratified audit selections and a population fingerprint. A reviewer can reproduce the selected IDs from the same population, approved sample counts, and committed seed.

## Run

Python 3.12+, standard library only:

```sh
python audit_sample.py population.example.json plan.example.json --seed ENG-001-approved-seed --output selection.json
python -m unittest discover -v
```

The output is created exclusively; an existing file is never overwritten. Exit 0 means a selection was written; 2 means invalid input or an I/O error.

## Method

Every population row has a unique string `id` and a nonempty `stratum`; other JSON metadata is retained in the canonical population fingerprint. Rows are sorted by ID and serialized as UTF-8 JSON with sorted keys and compact separators, then hashed with SHA-256. Nonfinite JSON numbers are rejected.

For each stratum, rank rows by SHA-256 of a domain-separated tuple containing the seed, population hash, stratum, and row ID. Select the first approved count without replacement. The report includes the population hash, seed, counts, selected IDs, and selection hashes. Input row order does not affect selection. Any population metadata change changes the fingerprint and may change selections.

The plan must cover every stratum explicitly, including any stratum assigned zero selections. Negative, noninteger, boolean, and oversized counts fail. A count equal to the stratum population provides full coverage of that stratum.

## Audit use

Freeze the complete population, validate reconciliation to the source system, agree strata and counts, and commit the seed through an independent reviewer before generating selections. Store the population, plan, selection output, and approval record under controlled evidence handling. An operator who can repeatedly change the seed can cherry-pick a sample; hashing alone does not prevent that. Avoid publishing real population records or identifying metadata.

This tool implements deterministic hash ranking, not a statistical confidence calculator. It does not choose a sample size, establish a confidence level, extrapolate error rates, or validate population completeness. Sampling methodology and sufficiency remain the auditor's responsibility.
