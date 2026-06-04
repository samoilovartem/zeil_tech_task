# Part 3 — Testing, Diagnosis & Collaboration

The brief says pick the angle I find most interesting and go deep. I will go deep on
**"how do I actually know a change is better"**, because I think this is the hardest and
most important part, and because I built a small eval harness in my prototype that shows my
thinking is real, not just words. Then I cover infra and QA more shortly.

## What "better retrieval" means

"Better" is meaningless until I define it with a number. So before I ship anything, I write
down what I expect to improve and how I will measure it. In my prototype I built an offline
eval harness exactly for this. It takes a set of labelled queries, runs them through the
full pipeline (retrieval + scoring), and prints metrics.

Real output from my harness:

```
query                                              p@k  rec@k   mrr  ndcg
Senior backend engineer, 5+ years Python, fin...   0.4    1.0   1.0   1.0
Python developer                                   0.4    1.0   1.0   1.0
truck driver near Parramatta                       0.6    1.0   1.0   1.0
AVERAGE                                           0.467   1.0   1.0   1.0
```

Small note that is actually important: precision@5 looks "low" (0.4–0.6). That is not a bug.
Each query only has 2–3 relevant candidates, so precision@5 can never be more than 3/5. This
is a normal trap with precision@k. The metric I trust most here is **nDCG**, which is 1.0 —
it means my ranking puts the graded-relevant people in the ideal order. I mention this
because Part 3 is really about *not being fooled by metrics*.

## The test set and where ground truth comes from

A test set is only useful if it is representative. My rules:

- **Cover the real query types**, not only easy ones. I deliberately put hard cases in my
  set: the "financial services" semantic case (where keywords fail), the Hanoi spelling
  variants, and the Parramatta proximity case.
- **Use graded labels** (0 = irrelevant, 1 = marginal, 2 = relevant, 3 = ideal), not just
  yes/no. This is what nDCG needs.

Where does ground truth come from at 800M scale? Two sources, and both are needed:

1. **Human judgments** — recruiters or trained raters label results for a sample of queries.
   This is the most trusted but small and slow.
2. **Implicit signals** — clicks, profile opens, "contact" actions, replies, and finally
   hires. This is huge but biased: people can only click what we showed them (position
   bias), so I cannot treat a click as pure truth. I would use implicit signals for scale
   and human labels to calibrate.

## Offline metrics vs production metrics — not the same

- **Offline:** nDCG@k, precision@k, recall@k, MRR. These measure ranking quality against
  labels.
- **Production:** recruiter engagement — contact rate, reply rate, and the real business
  metric, **hires / placements**.

They are not the same thing. Offline is a *proxy*. Online is the *real value*. A change can
look good offline and still fail online. That leads to the next question.

## "Precision went up offline, but engagement dropped in the A/B". How I diagnose it

This is the classic gap, and I would not panic. I would look at these causes, roughly in
order:

1. **My test set is not representative.** Maybe I improved the queries in my set but hurt
   common queries that are not in it. Fix: segment the A/B by query type and see which
   queries got worse.
2. **My labels do not match what recruiters actually want.** Maybe "relevant" to my rater is
   not "want to contact" to a recruiter. Fix: look at real losing cases, re-check labels.
3. **I optimised a proxy that does not drive behaviour.** Precision went up but I lost
   diversity, so results look more "samey" and recruiters click less. Fix: check result
   diversity, not only precision.
4. **Position bias / novelty effects** in the A/B itself.

The key tool is **segmentation**. An average hides the truth. I split the A/B by query type,
by region, by how rare the query is, and I look at *where* it regressed. Then I read actual
result lists for those queries. Diagnosis is mostly looking at concrete losing examples, not
staring at one average number.

## Retrieval problem vs scoring problem vs UI problem

My two-stage design (retrieval then re-rank) makes this measurable, which is a big reason I
built it that way:

- **Retrieval problem:** the right candidate is **not even in the top-N** from stage 1. I
  measure **recall@N at the retrieval stage**, before scoring. If recall is bad, no scoring
  fix can help — the candidate never arrives.
- **Scoring problem:** the right candidate **is** retrieved but ranked low after re-rank. I
  measure their **position after stage 2**. Retrieved but buried = scoring issue.
- **UI problem:** the candidate is ranked #2, looks correct, but recruiters still do not
  click. Then ranking is fine and the problem is presentation — the snippet, the summary,
  what we show on the card.

So I can point at the exact stage with numbers, instead of arguing by feeling. This is the
kind of thing I discussed with Jonathan — make the system measurable per stage, so we can
say "this is retrieval" or "this is scoring" with evidence.

## Working with infra — shipping safely at 800M

- **Change a mapping without reindexing everything:** usually you cannot change a field type
  in place. The safe pattern is **reindex into a new index, then swap an alias**. The app
  always points at an alias (e.g. `candidates`), and I move the alias from the old index to
  the new one in one atomic step. If it goes wrong, I move the alias back. No downtime.
- **Staging at this scale:** a **sampled index** (for example 1% of profiles) is good for
  catching crashes, mapping errors, and big regressions. But it lies about some things:
  rare-term statistics, tail queries, and anything that only appears at full scale. So I use
  the sample to catch obvious problems, and I trust full results only from a careful
  production rollout.
- **Day-one of a rollout:** I would ship behind a flag to a small percent of traffic. I
  instrument latency (p50/p95/p99), error rate, result counts (are we suddenly returning
  empty results?), and the engagement metrics. My **rollback trigger** is simple and decided
  in advance: if latency p95 or error rate crosses a line, or engagement drops past a
  threshold, roll back first and investigate after. Decide the trigger *before* shipping, not
  during the incident.

## Working with QA — making search testable

Search is hard to regression-test because results are subjective. My approach is to make it
concrete:

- **A good test case** = a query + the candidates that **must** appear (or must rank above
  others) + a clear pass/fail. Example I can hand to QA:
  *"For 'Senior Python financial services', candidate c1 must rank above c2 and c3.
  Pass = c1 is rank 1. Fail = anything else."* This is exactly what my eval harness checks.
- **Catching silent degradation:** this is the scary one — a change that fixes one query and
  quietly breaks five others. My answer is the **eval harness as a regression suite in CI**.
  A golden set of queries with expected ordering runs on every change. If average nDCG drops,
  or any "must rank above" rule breaks, the build fails. Silent degradation becomes loud.
- **Documenting a change** so someone outside the search team can verify it: I write down (1)
  what problem it fixes, (2) example queries before and after, (3) which metric should move
  and by how much, (4) how to run the eval to check. So a QA person or another engineer can
  reproduce it without reading my code.

## Why this matters

For me the main message of Part 3 is: a search change is a hypothesis, and I treat it like
one. I define the metric first, I build a test set with the hard cases in it, I measure per
stage so I can tell retrieval from scoring from UI, and I never trust one average number. The
eval harness in this prototype is the small but real proof that I work this way.

You can run it: `make eval`
