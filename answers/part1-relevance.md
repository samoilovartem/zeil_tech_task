# Part 1 — Relevant Experience Score

## Short version first

My main idea is simple: I do not score the candidate as one big blob of text. I score
**each experience separately**, then I combine them. A candidate is relevant when their
*recent and senior* roles match what the recruiter asked for. Old roles and off-topic
roles should count less, not the same.

I also want to say one thing early, because it shaped my whole approach. In my call with
Jonathan we talked about combining keyword search and semantic (vector) search. For this
task that is not just a nice extra — it is the thing that makes the example work at all.
I explain why below.

I built a small working prototype in OpenSearch to prove the idea is real. All the numbers
in this document come from the code actually running, not from my imagination.

## The example, and why the naive way fails

Query: *"Senior backend engineer, 5+ years Python, financial services"*

Candidate:
- Software Engineer @ Goldman Sachs · 2018–2021 · "Built trading APIs in Python and Java"
- Backend Lead @ Stripe · 2021–2024 · "Led payments infrastructure team, Python microservices"
- Freelance Developer · 2016–2018 · "Various web projects, mostly PHP"

Look at the words. The recruiter typed **"financial services"**. But this phrase is not in
the candidate text anywhere. The text says "trading", "Goldman Sachs", "payments",
"Stripe". A simple keyword search would give this candidate **zero** on the most important
part of the query. That is wrong. Goldman is a bank, Stripe is payments — both are
financial services.

This is why I use semantic matching. I checked it in code. I embedded the query and the
texts and measured similarity:

- "financial services" vs "Built trading APIs at Goldman Sachs" → **0.34**
- "financial services" vs "Various web projects, mostly PHP" → **0.16**

So the machine can see that trading at Goldman is much closer to financial services than
PHP web work. This is the difference between a naive solution and a real one.

## How I decide what is relevant and what is not

For each experience I calculate three "match" signals between 0 and 1:

- **skill_match** — does this role have the skill that was asked? (Python here)
- **domain_match** — is this role in the asked domain? (financial services here)
- **seniority_match** — does the role title meet the seniority floor? (Senior here)

Then I have two "weight" signals, also between 0 and 1:

- **recency_weight** — newer roles get more weight. I use a decay by years. Half-life 5
  years. So a role that ended this year is ~1.0, and an old role slowly goes down.
- **duration_weight** — longer roles get a bit more weight, but I cap it. A 10-year role
  should not crush everything else.

The relevance of one experience is a weighted sum:

```
relevance(e) = 0.45*skill + 0.35*domain + 0.20*seniority
contribution(e) = relevance(e) * recency_weight(e) * duration_weight(e)
```

I put skill highest (0.45) because the recruiter usually cares most about the skill.
Domain is second (0.35). Seniority is a smaller part (0.20) because the title alone is
weak signal. These weights are not magic — they are config, and in Part 3 I show how I
would tune them with real data.

The PHP freelance role gets skill=0 and domain=0. So its relevance is almost nothing. It
basically falls out by itself. I do not need a special rule to "remove" it. That is the
nice thing about per-experience scoring — irrelevant roles just score low.

## How I handle partial matches (Python in one role, not the other)

I do **not** require every role to match. I collect evidence across roles. Python is in
Goldman and in Stripe, but not in Freelance. That is fine. Each role is scored on its own,
and the good roles lift the candidate. A missing skill in one old role does not punish the
candidate.

For the "5+ years" part, I use a small gate. I add up the **years of Python across all
roles**: Goldman 3 years + Stripe 3 years = **6 years**. 6 ≥ 5, so the requirement is
**met**, and I give a bonus. This is exactly how a human recruiter reads a CV — they don't
need Python in every single job, they add it up.

## How recency, duration and seniority work together

Here is the real breakdown my code produced for this candidate (score is 0–100):

```
Score: 69.7   (python 5+ years: required 5, actual 6, MET)

Goldman Sachs (Software Engineer)   contribution 0.41
    skill 1.0 | domain 1.0 | seniority 0.5 | recency 0.50 | duration 0.90
Stripe (Backend Lead)               contribution 0.68
    skill 1.0 | domain 1.0 | seniority 1.0 | recency 0.76 | duration 0.90
Freelance (Freelance Developer)     contribution 0.03
    skill 0.0 | domain 0.0 | seniority 0.5 | recency 0.33 | duration 0.80
```

You can read the story directly:
- **Stripe is the strongest role.** It is recent (recency 0.76), it is a Lead so it meets
  Senior easily (seniority 1.0), it is fintech, and it has Python. Biggest contribution.
- **Goldman is good but older.** Same skill and domain, but recency is only 0.50 and the
  title "Software Engineer" is mid level, so seniority is 0.5 (one step below Senior).
- **Freelance almost disappears.** No Python, no finance, and it is old. Contribution 0.03.

So recency, duration and seniority are not separate scores I show at the end — they are
multipliers that shape how much each role is worth. This matches how I would explain a
candidate to a hiring manager.

## "6 years Python but it was not the only skill" — how it factors in

For this query the candidate also did Java, PHP, microservices, etc. I do **not** punish
that. The recruiter asked "5+ years Python", not "only Python". So what matters is: is
there enough Python depth, in recent and senior and in-domain roles? Yes. The other skills
are just normal — most senior people know more than one thing.

I would only treat this differently if the query was something like "Python **specialist**"
or "pure Python expert". Then I would care about how much of the career is Python vs other
things (a focus or density signal). It is a different question, so it needs a different
rule. Knowing this difference is important — same candidate, different query, different
score.

## Must-have vs nice-to-have skills (an honest limit of my scoring)

I want to be honest about something my own prototype shows, because a recruiter will notice
it. In my data there is a candidate with **no Python at all**, but Senior and in financial
services (a banking engineer in Java). My code gives him **37.3**. Another candidate **has**
Python, but he is Junior and not in finance. He gets **29.8**. So the no-Python person ranks
**above** the Python person.

Is this a bug? It depends what the recruiter really means. Right now all my signals are
**soft** — skill, domain and seniority are added together. The query asked three things, and
the Java banker matched two of them (Senior + finance), so he wins on points even with no
Python. That can be the correct behaviour, or it can be wrong.

It is wrong when the skill is a **must-have**, not a nice-to-have. If "5+ years Python" is a
hard requirement, then a person with zero Python should not show up at all, no matter how
senior. The fix is simple: turn that skill into a **hard filter** in the retrieval stage
(only keep people who have Python), instead of a soft score.

So my design can do both, and the recruiter chooses. By default I keep skills soft, so I do
not hide good people by accident. If the recruiter marks a skill as *required*, I switch it
to a hard filter. This is a small code change but a real product decision — exactly the kind
of thing I would agree with Jonathan and the team before shipping.

## Final output — one score or a breakdown?

I give **both**, on purpose:

- A **single score 0–100** (here 69.7). This is for ranking and sorting. Simple to use.
- A **full breakdown** (the table above) plus short text lines like
  *"Met python 5+ years (6 across roles)"*, *"Strongest role: Backend Lead at Stripe"*,
  *"Freelance role barely relevant"*.

Why both? Because a single number alone is not trustable. A recruiter will ask "why is
this person 69 and not 90?". The breakdown answers that. It also helps a lot in Part 3 —
when I want to debug or improve scoring, I can see which signal caused a result. A black-box
score is impossible to debug. As I said to Jonathan, I would rather ship something a bit
simpler that we can explain, than a clever score that nobody can defend.

## How it is built (system view)

Two stages, like real search systems:

1. **Retrieval (OpenSearch)** — get a wide set of candidates fast. I use hybrid: BM25
   keyword + kNN semantic, fused with Reciprocal Rank Fusion. This is the stage that makes
   sure the financial-services candidate is even found.
2. **Re-rank (Python)** — take the top candidates and run the scoring above, with the full
   breakdown. This stage is slower but only runs on a small set.

This separation is normal in production: cheap and wide first, expensive and precise after.
The honest trade-off: the re-ranker only sees the top-N from retrieval. So retrieval recall
must be good, or a great candidate never reaches the scoring step. I measure exactly this
in Part 3.

You can run it: `uv run zeil search "Senior backend engineer, 5+ years Python, financial services"`
