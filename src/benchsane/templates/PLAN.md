# Benchmark plan

Fill this in before running anything. Changing it after seeing results is fine, but note why.

## Decision
What will this number change? What effect size would change the decision?

## Claim
"On <host>, <candidate> is <effect> versus <baseline> for <workload>."

## Workload
Inputs, sizes and load levels. Why do they represent the real thing? Where should the change *not* help?

## Controlled or representative?
Pick one. Controlled: tuned host for a clean comparison. Representative: production settings, more runs.

## Procedure
- [ ] `benchsane doctor` is reviewed
- [ ] A/A noise floor measured
- [ ] Runs interleaved, in fresh processes, at least 30 blocks
- [ ] Output and error counts verified
- [ ] Limiter identified while running (what saturated?)

## Results
Link to the raw run directory. Absolute numbers and ratios, CI, n, host, commit.
