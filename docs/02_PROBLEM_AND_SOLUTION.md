# 02 · The Problem and How We Solve It, Step by Step

This guide explains **what problem we solve, why it matters, how we turned it into a mathematical model, how we solved it, and what the answers mean.** It also explains how the work is organised from start to finish.

> **Related guides**
> - [01_CODE_GUIDE.md](01_CODE_GUIDE.md): what every file contains
> - [03_DEMO_GUIDE.md](03_DEMO_GUIDE.md): the live demo
> - [04_FIGURES_GUIDE.md](04_FIGURES_GUIDE.md): the charts

---

## Part A: The Problem

### A1. The story

An AI company runs a chatbot (like ChatGPT or Claude). Every question a user types is answered by a **large language model running on GPUs**, and those GPUs sit in **data centers** around the world.

Our company has **4 GPU data centers**:

| Data center | Country | Character |
|---|---|---|
| **Mumbai** | India | Medium cost, close to India and the Middle East |
| **Singapore** | Singapore | Expensive, closest to Southeast Asia |
| **Frankfurt** | Germany | Most expensive, close to Europe |
| **Virginia** | USA | Cheapest, close to the USA |

Users come from **5 regions**: India, Southeast Asia, the Middle East, Europe and the USA.

The company must answer two questions:

> **Q1. Routing:** Which data center should answer which region's users, in every part of the day, so that the total cost is lowest?
>
> **Q2. Selection:** Should we keep all 4 data centers running, or switch some off for the day to save their fixed cost?

### A2. Why it is not obvious

1. **Capacity is limited.** Each data center can only answer so many queries per hour.
2. **Distance costs money.** Serving India from Virginia is slow (200 ms), and a slow answer is a worse product. We put a price on delay.
3. **Some routes are not allowed.** If the delay is above 150 ms (our quality promise, the *SLA*), that route is forbidden.
4. **Running costs differ by city.** Electricity, rent and GPU prices are different everywhere.
5. **Fixed costs.** A data center costs money every day just to stay on, even if it serves nobody.
6. **Demand moves with time zones.** India is busy when the USA is asleep and vice versa. A data center that is idle at one hour may be essential a few hours later.

So "everyone uses the nearest data center" does not work: the nearest one may be full, expensive, or not worth keeping on.

### A3. Is this a real problem?

Yes, in simplified form.
- Big cloud and AI companies (Google, Microsoft, Amazon, Cloudflare and others) constantly decide which data center serves which users. This is called **global load balancing**.
- GPUs for AI are expensive and scarce, so companies decide **in which regions to deploy a model at all**. For example, on Microsoft Azure, OpenAI models are offered only in some regions.
- Research has shown that routing requests to data centers with cheaper electricity saves a lot of money ("Cutting the Electric Bill for Internet-Scale Systems", SIGCOMM 2009).
- Closing or consolidating data centers because of fixed costs is a routine business decision.

**What we simplify:** real demand changes every second, real systems have thousands of servers and many models, and real routing is decided by software in milliseconds. We model a **planning version**: 4 data centers, 5 regions, 6 time blocks, one day.

### A4. Which course methods we use (and why only these two)

| Method | Where it appears |
|---|---|
| **Transportation Problem (a special Linear Program)** | Data centers = sources (supply), regions = destinations (demand), cost per unit on each route. We solve it with the **VAM hand method** and **optimally with Gurobi**. |
| **Integer Programming** | A **binary (0/1) ON/OFF decision** for each data center with a fixed cost. An LP cannot represent "on or off", so integer variables are needed. |

We deliberately use **only these two methods, applied thoroughly**, instead of touching every topic briefly.

---

## Part B: How we organised the work

```
 ┌──────────────┐   ┌───────────────┐   ┌─────────────────┐   ┌──────────────────┐
 │ 1. Define    │──►│ 2. Collect /  │──►│ 3. Formulate    │──►│ 4. Solve         │
 │   problem    │   │   design data │   │   maths model   │   │  (VAM + Gurobi)  │
 └──────────────┘   └───────────────┘   └─────────────────┘   └──────────────────┘
                                                                        │
 ┌──────────────┐   ┌───────────────┐   ┌─────────────────┐            │
 │ 7. Live demo │◄──│ 6. Visualise  │◄──│ 5. Analyse &    │◄───────────┘
 │  (pygame)    │   │  (4 figures)  │   │   compare plans │
 └──────────────┘   └───────────────┘   └─────────────────┘
```

| Stage | What we did | File |
|---|---|---|
| 1. Define | Chose the AI-serving problem, decided on 2 methods | this document |
| 2. Data | Capacities, costs, latencies, demand curves | `data.py` |
| 3. Formulate | Wrote variables, objective, constraints (Part 1 and Part 2) | `model.py` |
| 4. Solve | VAM by hand method and Gurobi for the optimum | `vam.py`, `model.py` |
| 5. Analyse | Step 0 to Step 4 comparisons | `main.py` |
| 6. Visualise | 4 charts | `charts.py` → `figures/` |
| 7. Demonstrate | Interactive what-if tool | `demo.py` |

---

## Part C: The Data (and why each number is reasonable)

All numbers are **synthetic but realistic**: chosen to reflect real-world patterns, not copied from a company.

### C1. Units
- Queries: **thousand per hour** (`150` = 150,000 queries/hour)
- Money: **US $**
- Time: **6 blocks × 4 hours** in IST

### C2. Data centers (supply)

| | Capacity (k/h) | Serving cost ($/1000 q) | Fixed cost ($/day) | Why |
|---|---|---|---|---|
| Mumbai | 200 | 1.10 | 3,000 | Lower land and labour cost |
| Singapore | 130 | 1.40 | 3,500 | Small, land and power are expensive |
| Frankfurt | 170 | 1.50 | 4,000 | German electricity is among the most expensive |
| Virginia | 220 | 0.90 | 3,500 | Largest cloud hub in the world, cheap power |
| **Total** | **720** | | **14,000** | |

### C3. Demand (thousand queries/hour)

| Region | 00-04 | 04-08 | 08-12 | 12-16 | 16-20 | 20-24 | Daily avg |
|---|---|---|---|---|---|---|---|
| India | 41 | 41 | 107 | 120 | **139** | 131 | 96.5 |
| Southeast Asia | 16 | 46 | 71 | 75 | **89** | 51 | 58.0 |
| Middle East | 29 | 11 | 34 | 48 | 51 | **59** | 38.7 |
| Europe | **119** | 44 | 31 | 87 | 104 | 117 | 83.7 |
| USA | 157 | **185** | 124 | 36 | 86 | 147 | 122.5 |
| **Total** | 362 | 327 | 367 | 366 | 469 | **505** | 399.3 |

**How it was designed:** every region follows the same daily shape *in its own local time* (quiet at 3–5 am, rising in the morning, peak around 7–10 pm). Converting each region's local time into IST shifts the peaks, so the busy period "travels" around the world. Bold = each region's peak block.

### C4. Latency, the SLA and the cost formula

**Cost of serving 1000 queries from data center *i* to region *j*:**

$$c_{ij} = \text{serving cost}_i + 0.005 \times \text{latency}_{ij}\ (\text{ms})$$

Example: Mumbai → India = 1.10 + 0.005 × 20 = **$1.20**

**SLA rule:** if latency > 150 ms, the route is **prohibited**.

| Latency (ms) | India | SE Asia | Middle East | Europe | USA |
|---|---|---|---|---|---|
| Mumbai | 20 | 60 | 40 | 120 | ~~200~~ |
| Singapore | 60 | 15 | 90 | ~~160~~ | ~~220~~ |
| Frankfurt | 120 | ~~160~~ | 80 | 15 | 90 |
| Virginia | ~~200~~ | ~~220~~ | ~~170~~ | 85 | 20 |

**Final cost table ($ per 1000 queries), the input to the transportation problem:**

|  | India | SE Asia | Middle East | Europe | USA | **Supply** |
|---|---|---|---|---|---|---|
| Mumbai | 1.200 | 1.400 | 1.300 | 1.700 | ✗ | 200 |
| Singapore | 1.700 | 1.475 | 1.850 | ✗ | ✗ | 130 |
| Frankfurt | 2.100 | ✗ | 1.900 | 1.575 | 1.950 | 170 |
| Virginia | ✗ | ✗ | ✗ | 1.325 | 1.000 | 220 |

13 of the 20 routes are allowed. Note two important facts:
- **SE Asia** can only be served by Mumbai or Singapore.
- **USA** can only be served by Virginia or Frankfurt.

---

## Part D: The Mathematical Model

### D1. Notation

| Symbol | Meaning |
|---|---|
| $i$ | data center (Mumbai, Singapore, Frankfurt, Virginia) |
| $j$ | region (India, SE Asia, Middle East, Europe, USA) |
| $t$ | time block (00-04, …, 20-24) |
| $A$ | set of **allowed** routes $(i,j)$ (latency ≤ 150 ms) |
| $S_i$ | capacity (supply) of data center $i$ (k/h) |
| $D_{jt}$ | demand of region $j$ in block $t$ (k/h) |
| $c_{ij}$ | cost per 1000 queries on route $i \to j$ |
| $F_i$ | fixed cost per day of keeping $i$ ON |
| $H$ | hours per block = 4 |

### D2. Part 1: Transportation Problem (LP)

**Decision variable**
$$x_{ijt} \ge 0 \quad = \text{thousand queries/hour sent from } i \text{ to } j \text{ in block } t, \quad (i,j) \in A$$

**Objective: minimise the daily cost**
$$\min \; Z = H \sum_{t}\sum_{(i,j)\in A} c_{ij}\, x_{ijt} \;+\; \sum_i F_i$$
(All data centers are ON in Part 1, so $\sum F_i = 14{,}000$ is just a constant.)

**Constraints**
$$\sum_{j:(i,j)\in A} x_{ijt} \le S_i \qquad \forall i, t \qquad \text{(supply / capacity)}$$
$$\sum_{i:(i,j)\in A} x_{ijt} = D_{jt} \qquad \forall j, t \qquad \text{(demand must be met)}$$
$$x_{ijt} \ge 0$$

This is exactly the classroom transportation problem (sources → destinations, supply ≤, demand =), **repeated for 6 time blocks**.

**Why it is unbalanced:** total supply (720) is always greater than total demand (at most 505). In the hand method we add a **dummy column**. In Gurobi the "≤" supply constraint handles this automatically.

### D3. Part 2: Integer Programming (data center selection)

**New variable**
$$y_i \in \{0, 1\} \quad = 1 \text{ if data center } i \text{ is ON for the whole day}$$

**Objective**
$$\min \; Z = H \sum_{t}\sum_{(i,j)\in A} c_{ij}\, x_{ijt} \;+\; \sum_i F_i\, y_i$$

**Constraints**
$$\sum_{j} x_{ijt} \le S_i\, y_i \qquad \forall i, t \qquad \text{(OFF} \Rightarrow \text{capacity 0)}$$
$$\sum_{i} x_{ijt} = D_{jt} \qquad \forall j, t$$
$$x_{ijt} \ge 0, \quad y_i \in \{0,1\}$$

**The key idea:** multiplying the capacity by $y_i$ links the two decisions. If $y_i = 0$, the data center's capacity becomes 0, so nothing can be routed from it, but we also don't pay its fixed cost.

**Why $y_i$ is one decision for the whole day (not per block):** you cannot realistically switch a data center on and off every 4 hours. The ON/OFF decision is daily; the routing decision is per block. This is what links the 6 blocks into **one** model.

### D4. Model size

| | Part 1 (LP) | Part 2 (IP) |
|---|---|---|
| Continuous variables $x$ | 78 (13 routes × 6 blocks) | 78 |
| Binary variables $y$ | 0 | 4 |
| Supply constraints | 24 (4 × 6) | 24 |
| Demand constraints | 30 (5 × 6) | 30 |

### D5. How Gurobi solves it
- **Part 1 (LP):** simplex-type algorithms (the same idea as the simplex method from class: move from corner point to corner point of the feasible region until no better one exists). The answer is **guaranteed optimal**.
- **Part 2 (IP):** **branch-and-bound.** Gurobi solves the LP relaxation (pretending $y$ can be fractional). If some $y$ comes out fractional (e.g. 0.4), it **branches** into two sub-problems ($y=0$ and $y=1$) and keeps the best whole-number solution, cutting off branches that cannot beat it.
- With 4 binaries there are only $2^4 = 16$ ON/OFF combinations, so the result can even be checked by brute force (we checked every single-OFF case in Step 3 below). Both solve in **milliseconds**.

---

## Part E: Solving It, Step by Step (what `main.py` does)

### Step 0: Build the cost table
Compute $c_{ij}$ for all routes and mark prohibited ones (table C4). This is the input to every later step.

### Step 1: One block: VAM vs optimal

We take the **busiest block, 20-24 IST**, and solve it as a single transportation problem (per hour).

- Supply = 200 + 130 + 170 + 220 = **720**
- Demand = 131 + 51 + 59 + 117 + 147 = **505**
- **Unbalanced** → add a **Dummy** column with demand **215** and cost 0
- Prohibited routes get cost **M = 1000** (Big-M)

**VAM trace (exactly as the program computes it):**

| Step | Largest penalty | Chosen cell (cheapest in that row/col) | Amount |
|---|---|---|---|
| 1 | 1.575 on **row Frankfurt** | Frankfurt → Dummy (cost 0) | 170 |
| 2 | 999 on **column USA** | Virginia → USA (1.000) | 147 |
| 3 | 1.475 on **row Singapore** | Singapore → Dummy (0) | 45 |
| 4 | 998.675 on **row Virginia** | Virginia → Europe (1.325) | 73 |
| 5 | 998.3 on **column Europe** | Mumbai → Europe (1.700) | 44 |
| 6 | 0.55 on **column Middle East** | Mumbai → Middle East (1.300) | 59 |
| 7 | 0.50 on **column India** | Mumbai → India (1.200) | 97 |
| 8 | 1.70 on **column India** | Singapore → India (1.700) | 34 |
| 9 | 1.475 on **row Singapore** | Singapore → SE Asia (1.475) | 51 |

9 allocations = $m + n - 1 = 4 + 6 - 1 = 9$, so the solution is **non-degenerate** (a valid basic feasible solution).

**Comparison:**

| | Mumbai | Singapore | Frankfurt | Virginia | **Cost/hour** |
|---|---|---|---|---|---|
| **VAM** | India 97, ME 59, Europe 44 | India 34, SEA 51 | idle (all to dummy) | Europe 73, USA 147 | **$644.65** |
| **Gurobi optimal** | India 131, SEA 10, ME 59 | SEA 41 | Europe 44 | Europe 73, USA 147 | **$621.40** |

**VAM is 3.74% above the optimum.**
*Why:* in step 1 the zero-cost dummy column made Frankfurt's penalty the largest, so VAM sent all of Frankfurt to "idle". Europe's leftover 44 then had to come from Mumbai ($1.70 instead of $1.575), and India had to use expensive Singapore ($1.70 instead of $1.20).
**Lesson:** VAM gives a good *starting* solution, but an optimality method (MODI/stepping stone by hand, or simplex in Gurobi) is needed for the true optimum.

### Step 2: Part 1: full-day transportation LP (all ON)

| | Value |
|---|---|
| Routing cost | $11,696 |
| Fixed cost (all 4 ON) | $14,000 |
| **Total** | **$25,696 / day** |

**Observation:** Frankfurt is barely used. It only serves Europe in 3 blocks (56, 9 and 44 k/h), using **33%, 5% and 26%** of its capacity, and **0%** in the other 3 blocks. We pay $4,000/day to keep it on. This motivates Part 2.

### Step 3: Part 2: Integer Programming (choose ON/OFF)

| | Value |
|---|---|
| Decision | Mumbai **ON**, Singapore **ON**, Frankfurt **OFF**, Virginia **ON** |
| Routing cost | $11,822 (+$126 vs Part 1) |
| Fixed cost | $10,000 (−$4,000) |
| **Total** | **$21,822 / day** |
| **Saving vs Part 1** | **$3,874 / day (15.1%)** |

**Optimal routing plan (thousand queries/hour):**

| Block | Mumbai serves | Singapore serves | Virginia serves |
|---|---|---|---|
| 00-04 | India 41, SEA 16, ME 29, Europe 56 | — | Europe 63, USA 157 |
| 04-08 | India 41, SEA 46, ME 11, Europe 9 | — | Europe 35, USA 185 |
| 08-12 | India 107, SEA 59, ME 34 | SEA 12 | Europe 31, USA 124 |
| 12-16 | India 120, SEA 32, ME 48 | SEA 43 | Europe 87, USA 36 |
| 16-20 | India 139, SEA 10, ME 51 | SEA 79 | Europe 104, USA 86 |
| 20-24 | India 97, ME 59, Europe 44 | India 34, SEA 51 | Europe 73, USA 147 |

**Capacity used (%):**

| | 00-04 | 04-08 | 08-12 | 12-16 | 16-20 | 20-24 |
|---|---|---|---|---|---|---|
| Mumbai | 71 | 54 | 100 | 100 | 100 | 100 |
| Singapore | 0 | 0 | 9 | 33 | 61 | 65 |
| Frankfurt | OFF | OFF | OFF | OFF | OFF | OFF |
| Virginia | 100 | 100 | 70 | 56 | 86 | 100 |

**Reading the plan:**
- **Virginia** (cheapest) is always busy: full at night in IST, when the USA and Europe are awake.
- **Mumbai** is full from 8 am to midnight IST, when India is awake. At night it has spare capacity, so it **helps Europe** (56 k/h at 00-04): *"follow the sun"*.
- **Singapore** is idle at night but needed in the afternoon and evening when Asia peaks. It stays ON because the decision is for the whole day.

#### Why Frankfurt is OFF

1. **Most expensive**: highest fixed cost ($4,000) and highest serving cost ($1.50).
2. **Every region it can serve has a cheaper option**: Europe from Virginia ($1.325 vs $1.575), USA from Virginia ($1.00 vs $1.95), India from Mumbai ($1.20 vs $2.10), Middle East from Mumbai ($1.30 vs $1.90).
3. **Switching it off costs only +$126/day in routing but saves $4,000/day.**

**Checking every alternative (one data center forced OFF, the rest optimised):**

| OFF | ON | Cost/day | Unserved |
|---|---|---|---|
| **Frankfurt** | Mumbai, Singapore, Virginia | **$21,822** ✅ cheapest | 0 |
| Singapore | Mumbai, Frankfurt, Virginia | $22,598 | 0 |
| Mumbai | Singapore, Frankfurt, Virginia | $24,876 | 0 |
| Virginia | Mumbai, Singapore, Frankfurt | $25,540 | **80k** (USA) |

**Why not switch off two?** Peak demand is 505 k/h, and the largest two data centers together (Virginia 220 + Mumbai 200) give only 420. At least **3** must stay ON.

### Step 4: Why dynamic demand matters (static vs dynamic)

**Question:** what if we planned with only the **daily average** demand (399 k/h) instead of the 6 blocks?

1. Solve the IP with average demand over one 24-hour block.
   → It keeps only **Mumbai + Virginia** (capacity 420 ≥ 399). Cost on paper: routing $11,535 + fixed $6,500 = **$18,035/day**. This looks cheaper.
2. **Test that decision against the real block-by-block demand** (fix ON/OFF, allow unserved demand):

| Block | Unserved (k/h) | Region |
|---|---|---|
| 08-12 | 12 | Southeast Asia |
| 12-16 | 43 | Southeast Asia |
| 16-20 | 79 | Southeast Asia |
| 20-24 | 41 + 44 = 85 | Southeast Asia + Europe |
| **Day total** | **876 thousand queries lost** | |

**Why it fails:** on average Mumbai's 200 is enough for India + SE Asia + Middle East (193). But at 16-20 those three need **279**. SE Asia can only be served by Mumbai or Singapore, and Singapore is OFF, so SE Asia users go unanswered. At 20-24 total demand (505) exceeds the remaining capacity (420) by exactly 85.

**Conclusion:** a plan built on averages is **cheaper on paper but fails at peak hours**. The dynamic (multi-period) model sees the peaks and keeps Singapore ON. That is the value of modelling demand block by block.

---

## Part F: Final Answer (in one paragraph)

> Keep **Mumbai, Singapore and Virginia ON** and switch **Frankfurt OFF**. Route queries as in the Step 3 table: Virginia serves the USA and most of Europe, Mumbai serves India and the Middle East (and helps Europe at night), and Singapore serves Southeast Asia at its peaks. **Total cost: $21,822/day**, a **15.1% saving ($3,874/day, about $1.4 million/year)** over keeping all data centers on, with **every query served within the 150 ms SLA**. Planning on average demand instead would lose **876,000 queries per day**.

(Daily traffic ≈ 9.58 million queries, so the optimal plan costs about **$2.28 per 1000 queries**.)

---

## Part G: Assumptions and Limitations

| Assumption | Reality | Effect |
|---|---|---|
| Demand is known for each 4-hour block | Demand is uncertain and changes each second | Could add forecasting or a safety margin |
| Capacity is fixed per data center | GPUs can be added or rented | Could make capacity a decision too |
| One model type, all queries equal | Different model sizes and query types | Could add query classes |
| Cost is linear in volume | Bulk discounts, etc. | Fine for a planning model |
| Data is synthetic | Real company data is private | The model works unchanged with real data |
| ON/OFF once per day | Could be weekly or monthly | Same structure, different horizon |

## Part H: Possible Extensions
- Carbon emissions: add CO₂ per data center and a carbon cap or price.
- Uncertain demand: plan for several demand scenarios (stochastic programming).
- More time blocks (24 hourly blocks) and more regions. The model scales with no code change.
- Capacity expansion: decide how many GPUs to buy for each site (integer variables).

---

## Part I: Likely Viva Questions

| Question | Answer |
|---|---|
| Why is this a transportation problem? | Sources with supply (data centers), destinations with demand (regions), a cost per unit on each route, minimise total cost. |
| Is it balanced? | No. Supply 720 > demand (max 505). By hand we add a dummy column. In Gurobi the ≤ supply constraints handle it. |
| How do you handle prohibited routes? | By hand: cost = Big-M (1000). In Gurobi: we simply don't create those variables. |
| Why do you need integer programming? | ON/OFF is a yes/no decision with a fixed cost. An LP can't represent "pay $4,000 only if you use it at all". |
| What does $x \le S \cdot y$ do? | If $y=0$ the capacity is 0, so no flow is possible. If $y=1$ the normal capacity applies. |
| Why is $y$ daily and not per block? | Data centers can't realistically be switched every 4 hours. It also links the 6 blocks into one decision. |
| How does Gurobi solve the IP? | Branch-and-bound on the LP relaxation (plus cuts and heuristics). |
| Why is VAM not optimal? | It is a heuristic for a starting solution. Here it is 3.74% above optimal because the zero-cost dummy column misled its penalties. |
| Why is Frankfurt OFF? | Highest costs, a cheaper alternative for every region it serves, +$126 routing vs −$4,000 fixed. |
| Why not switch off two? | Peak 505 > best pair 420. |
| Why model dynamic demand? | The average-based plan loses 876k queries/day at peaks. |
| Is the data real? | Synthetic but realistic. The model works unchanged with real data. |
| How big is the model? | 78 continuous + 4 binary variables, 54 constraints, solved in milliseconds. |
