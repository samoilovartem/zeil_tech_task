# Part 2 — Location Filter at Scale

## The core idea

Matching location as text is a trap. "Hanoi", "Ha noi", "Hà Nội", "Vietnam - Hanoi" are
the same place but different strings. If I try to fix this with fuzzy text matching at
search time, it will be slow and noisy, and at 800M profiles it will not work.

So my core idea is: **turn messy location text into one canonical place at ingest time,
and match on that canonical place at search time.** Do the hard work once, when the profile
comes in. Not 800 million times per query.

I built this in the prototype and it works. I show real output below.

## Step 1 — normalise and resolve at ingest

When a profile arrives, I clean the location string in three steps:

1. **Fold the text** — Unicode normalise, remove accents, lowercase, collapse symbols.
   So "Hà Nội" becomes "ha noi", and "Vietnam - Hanoi" becomes "vietnam hanoi".
2. **Apply synonyms** — for variants that are not just accents. For example "Saigon" and
   "Ho Chi Minh City" share no letters, so folding cannot connect them. A small alias
   table handles these.
3. **Resolve in a gazetteer** — a place database. I look up the folded/aliased string and
   get back a **canonical id**, the place **hierarchy** (suburb → city → region → country),
   **coordinates**, and a **confidence**.

Real output from my code (all three variants resolve to the same id):

```
"Hà Nội"          -> id=vn-hanoi  level=city
"Ha noi"          -> id=vn-hanoi  level=city
"Vietnam - Hanoi" -> id=vn-hanoi  level=city
"Atlantis"        -> id=None      level=unresolved  confidence=0.0
```

Important: I keep the **raw** string too, and a **confidence** number. I never throw away
the original. If my gazetteer improves later, I can re-run resolution. And if something is
unknown (like "Atlantis"), I mark it unresolved instead of guessing.

## Step 2 — match at query time

When a recruiter searches "Hanoi", I run the **same** fold + synonym + resolve on the query.
It becomes `vn-hanoi`. Then I just match `location_id = vn-hanoi`. All the variant profiles
match, because they were all resolved to the same id at ingest. No fuzzy matching at search
time, no noise.

This is the key point I made to Jonathan: the cleverness happens **once at ingest**, so the
query stays a cheap exact lookup. That is what makes it possible at 800M.

## The 2–3 biggest problems at 800M, and how I solve them

1. **You cannot do expensive matching per query.** Fuzzy matching 800M rows for every
   search is impossible. Solution: resolve at ingest, store a `keyword` canonical id, and
   the query is a fast term lookup. This is the single most important decision.

2. **Location is a filter, not a score.** "In Hanoi or not" is yes/no. I put it in the
   filter part of the query, not the scoring part. OpenSearch caches filters as bitsets, so
   the same filter is reused and very fast. I do not waste scoring math on a yes/no field.

3. **The long tail and ambiguity.** Same name in many places ("Springfield"), and one place
   with many names. Solution: the gazetteer with hierarchy and confidence. Keep raw text so
   I can reprocess. Accept that some long-tail places will be unresolved and handle that
   honestly (see fallback below).

## What breaks first when you go global

Scripts and languages break first. Latin, Cyrillic, Chinese, Arabic, Devanagari. "Москва"
and "Moscow" are the same city in two scripts. Accents are easy (I already fold them), but
full transliteration between scripts is harder. Region naming is also different per country
(suburb vs district vs ward). My honest answer: in the prototype I solve accents + synonyms
+ a gazetteer for the main places. Full cross-script transliteration I would describe as the
next step, not pretend I solved it in code.

## Bonus — suburb-level search (truck drivers near Parramatta)

This is a different problem, because here **distance matters**. A driver two suburbs away is
useful, across the city is not. But most profiles do not have GPS coordinates.

My approach: **resolve to the finest place I can, and use that place's centre point as an
approximate coordinate.** I also keep a `granularity` tag (suburb / city / region / country).
So even a profile that only says "Parramatta" gets a coordinate (the centre of Parramatta),
which is good enough to measure "near".

Then the rule for **surface vs exclude**:

- If the profile resolves to a **suburb or city** (has a trustable point) → I rank it by
  distance, with a steep decay. Close = high score, far = low.
- If the profile only says **"NSW"** or **"Australia"** → this is too vague for a job where
  proximity is critical. I **exclude it** (or I could show it in a separate "location not
  confirmed" group). I do **not** fake a distance for it.

Real output from my code, query "truck driver near Parramatta":

```
17.8  Parramatta Trucker      (at the target)
17.8  Harris Park Trucker     (~1 km away)
16.8  Blacktown Trucker       (further out)
11.9  Bondi Trucker           (across the city)
 0.0  Hanoi Variant B         (a "truck driver", but in Hanoi -> ~7000 km -> 0)
 0.0  Vague Australia Trucker (only "Australia" -> too vague, excluded)
```

This is exactly what we want. Near suburbs rank high, far suburb (Bondi) ranks low, and the
vague "Australia" profile is dropped. The fallback when location is too vague is: do not
pretend. Be honest that we cannot confirm proximity.

Two profiles get **0.0, but for two different reasons** — and I think this is a good thing to
show, not hide. The "Australia" profile is dropped because it is **too vague** (granularity).
The Hanoi profile is dropped because it is **too far** (distance ~7000 km, so the decay is
basically zero).

But why is a Hanoi driver in a "near Parramatta" search at all? Because for a proximity
search I do **not** filter by exact location id at retrieval. If I did, I would lose a driver
in a neighbouring suburb who did not write exactly "Parramatta". So I let geo distance decide
instead. The price is that some far profiles whose text says "truck driver" get pulled into
the pool and then score zero.

In production I would fix this with a **geo bounding box at retrieval** — for example only
fetch profiles within ~100 km of Parramatta. Then Hanoi never enters the pool, and I would
also hide the zero-score rows from the recruiter. In the prototype I left them visible on
purpose, because the two different zeros show the logic is really working.

## Smarter at ingest — and the risks

Yes, enriching at ingest is the smart move, and it is what I built. But it has risks:

- **Wrong resolution.** If I map an ambiguous name to the wrong place, every search after
  that is wrong, silently. This is why I store **confidence** and keep the **raw** value, so
  I can re-check and re-run. I would rather mark something low-confidence than guess high.
- **Over-normalising.** If I am too aggressive, I can merge two different places into one.
  So I am careful and keep the hierarchy.

## How scoring changes: proximity role vs remote role

This is an important point. The **same** location data is used differently depending on the
job:

- **Truck driver (proximity critical):** location is a **dominant** factor. I multiply the
  score by a distance decay, and I exclude vague profiles. Far away = basically zero.
- **Remote-friendly role:** location is a soft preference or not a factor at all. In my code,
  if the search is not proximity-based, `apply_proximity` just returns the original score
  unchanged. Location does not punish anyone.

So I parameterise the location weight by the query intent. One engine, two behaviours.

## What I would cut: 2 weeks vs 2 months

- **2 weeks:** accent/Unicode folding, a synonym table for the top cities, gazetteer
  resolution for major places, and `geo_distance` for profiles that resolve to a point.
  This already handles the Hanoi case and the Parramatta case. **Cut:** full cross-script
  transliteration, ML geocoding of messy free text, a complete worldwide suburb gazetteer.
- **2 months:** add transliteration across scripts, an ML/geocoding step for the messy
  free-text addresses, a full hierarchical gazetteer, confidence tuning, and a re-enrichment
  pipeline so old profiles get upgraded when the gazetteer improves.

You can run it: `make search Q="truck driver near Parramatta" PROX=30`
