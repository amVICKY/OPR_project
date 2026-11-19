# 01 · Code Guide: What Every File Does

This guide explains **every file in the project**: what it contains, what each part of the code does, and how the files work together.

> **Related guides**
> - [02_PROBLEM_AND_SOLUTION.md](02_PROBLEM_AND_SOLUTION.md): the problem, the maths, and the step-by-step solution
> - [03_DEMO_GUIDE.md](03_DEMO_GUIDE.md): the live pygame demo
> - [04_FIGURES_GUIDE.md](04_FIGURES_GUIDE.md): the four charts

---

## 1. Project at a glance

**Project title:** *AI Query Routing across GPU Data Centers*
**Methods used:** Transportation Problem (Linear Programming) + Integer Programming
**Solver:** Gurobi (academic license)
**Language:** Python 3.11

```
OPR_project/
│
├── data.py            ← ALL input numbers (capacities, costs, demand, latency)
├── model.py           ← The optimisation model (Part 1 LP and Part 2 IP)
├── vam.py             ← Vogel's Approximation Method (hand method from class)
├── main.py            ← Runs the full study step by step and prints results
├── charts.py          ← Draws the 4 report figures
├── demo.py            ← Live interactive demo (pygame)
│
├── figures/           ← PNG charts created by main.py
│   ├── 1_demand.png
│   ├── 2_cost_comparison.png
│   ├── 3_utilization.png
│   └── 4_static_plan_failure.png
│
├── docs/              ← These four guides
├── environment.yml    ← Conda environment (which libraries to install)
├── .gitignore         ← Files git must never upload (e.g. the Gurobi license)
└── info.txt           ← The original assignment brief (not uploaded to git)
```

### How the files depend on each other

```
                    data.py
                (all the numbers)
                 │     │     │
        ┌────────┘     │     └─────────┐
        ▼              ▼               ▼
    model.py        vam.py         charts.py
  (Gurobi model)  (hand method)   (matplotlib)
        │              │               │
        ├──────────────┴───────────────┤
        ▼                              │
     main.py  ◄────────────────────────┘
 (report: Steps 0-4 + charts)

     demo.py  ── uses data.py + model.py  (live pygame window)
```

- `data.py` imports nothing from the project. It is the single source of truth for every number.
- `model.py`, `vam.py` and `charts.py` each read from `data.py`.
- `main.py` and `demo.py` are the two **programs you run**. Everything else is a building block.

Because both programs use the **same** `data.py` and `model.py`, the report and the demo always give the same answers. If you change a number in `data.py`, both update automatically.

### Libraries used

| Library | Why it is needed | Used in |
|---|---|---|
| `gurobipy` | Builds and solves the LP / IP models | `model.py` |
| `matplotlib` | Draws the PNG charts | `charts.py` |
| `pygame` | Draws the live animated demo window | `demo.py` |
| `math`, `time`, `os` | Python built-ins (distance, timer, folders) | `demo.py`, `charts.py` |

We use no pandas, numpy or seaborn, on purpose. The code uses only plain Python lists and dictionaries so every line is easy to read and explain.

---

## 2. `data.py`: all input data

**Purpose:** holds every number the problem needs, in plain Python dictionaries and lists. No calculations happen here except a few tiny helper functions.

### 2.1 Units (written at the top of the file)
| Quantity | Unit |
|---|---|
| Queries | **thousand queries per hour** (e.g. `150` = 150,000 queries/hour) |
| Money | **US dollars ($)** |
| Time | The day is split into **6 blocks of 4 hours**, in Indian Standard Time (IST) |

### 2.2 Sources: the data centers

```python
DATA_CENTERS = ["Mumbai", "Singapore", "Frankfurt", "Virginia"]
```

| Variable | Meaning | Mumbai | Singapore | Frankfurt | Virginia |
|---|---|---|---|---|---|
| `CAPACITY` | Max queries it can answer (thousand/hour) | 200 | 130 | 170 | 220 |
| `SERVING_COST` | GPU + electricity cost ($ per 1000 queries) | 1.10 | 1.40 | 1.50 | 0.90 |
| `FIXED_COST` | Cost of keeping it ON for one day ($) | 3000 | 3500 | 4000 | 3500 |

- **Capacity** is the *supply* in transportation-problem language.
- **Serving cost** reflects local electricity and GPU rental prices. Virginia (USA) is cheapest. Frankfurt (Germany, expensive electricity) and Singapore (expensive land and power) are the most costly.
- **Fixed cost** is paid just for keeping the site running (rent, cooling, staff, idle GPUs), even if it serves zero queries. It is what makes Part 2 (Integer Programming) necessary.

### 2.3 Destinations: user regions

```python
REGIONS = ["India", "Southeast Asia", "Middle East", "Europe", "USA"]
```

These are the *destinations* in the transportation problem. Each region has a demand that changes through the day.

### 2.4 Time blocks

```python
BLOCKS = ["00-04", "04-08", "08-12", "12-16", "16-20", "20-24"]   # IST
HOURS_PER_BLOCK = 4
```

The day is cut into 6 blocks. The model makes a separate routing plan for each block. `HOURS_PER_BLOCK` turns an hourly cost into a cost for the block (cost per hour × 4).

### 2.5 Demand (the dynamic part)

```python
DEMAND = {
    #                  00-04 04-08 08-12 12-16 16-20 20-24
    "India":          [41,   41,   107,  120,  139,  131],
    "Southeast Asia": [16,   46,   71,   75,   89,   51],
    "Middle East":    [29,   11,   34,   48,   51,   59],
    "Europe":         [119,  44,   31,   87,   104,  117],
    "USA":            [157,  185,  124,  36,   86,   147],
}
```

- Each list has **6 numbers, one per time block**, in thousand queries/hour.
- Every region is busiest in **its own local evening** and quietest in its local early morning. Because the regions are in different time zones, **their peaks happen at different IST times**. For example:
  - USA peaks at **04-08 IST** (185), which is evening in New York.
  - India peaks at **16-20 IST** (139).
  - Europe is high at **00-04 IST** (119), which is late evening in Europe.
- Total demand per block: **362, 327, 367, 366, 469, 505**. The busiest block is **20-24 IST (505)**.

### 2.6 Latency (network delay)

```python
LATENCY = {
    #             India  SE Asia  Mid East  Europe  USA
    "Mumbai":    [20,    60,      40,       120,    200],
    "Singapore": [60,    15,      90,       160,    220],
    "Frankfurt": [120,   160,     80,       15,     90],
    "Virginia":  [200,   220,     170,      85,     20],
}
MAX_LATENCY = 150        # SLA
LATENCY_PENALTY = 0.005  # $ per ms per 1000 queries
```

- Approximate round-trip delay in **milliseconds** between each data center and each region (nearby means low, other side of the world means high).
- `MAX_LATENCY = 150` is the **Service Level Agreement (SLA)**. A route slower than 150 ms is **not allowed** (a *prohibited route* in transportation-problem terms).
- `LATENCY_PENALTY = 0.005` puts a money value on slowness: every millisecond adds $0.005 per 1000 queries, because a slower answer is a worse user experience.

### 2.7 Helper functions

| Function | What it returns | Example |
|---|---|---|
| `latency(dc, region)` | Delay in ms for that pair | `latency("Mumbai", "India")` → `20` |
| `route_allowed(dc, region)` | `True` if latency ≤ 150 ms | `route_allowed("Singapore", "USA")` → `False` (220 ms) |
| `cost(dc, region)` | Cost of serving 1000 queries = `SERVING_COST + 0.005 × latency` | `cost("Mumbai","India")` = 1.10 + 0.005×20 = **1.20** |
| `demand_of_block(block)` | Demand of every region in one block | `demand_of_block("20-24")` → `{"India":131, ...}` |
| `average_demand()` | One number per region = average over the day (for the "static" comparison) | India → 96.5 |

**Resulting cost table (`cost()` for every pair), $ per 1000 queries:**

|  | India | SE Asia | Middle East | Europe | USA |
|---|---|---|---|---|---|
| **Mumbai** | 1.200 | 1.400 | 1.300 | 1.700 | ✗ |
| **Singapore** | 1.700 | 1.475 | 1.850 | ✗ | ✗ |
| **Frankfurt** | 2.100 | ✗ | 1.900 | 1.575 | 1.950 |
| **Virginia** | ✗ | ✗ | ✗ | 1.325 | 1.000 |

✗ = prohibited (latency above 150 ms). Out of 20 possible routes, **13 are allowed**.

---

## 3. `model.py`: the optimisation model

**Purpose:** builds the mathematical model in Gurobi, solves it, and stores the answer. **One class handles both parts of the project.**

### 3.1 Quiet Gurobi environment

```python
ENV = gp.Env(empty=True)
ENV.setParam("OutputFlag", 0)
ENV.start()
```

Creates a single Gurobi environment with output switched off. This hides Gurobi's solver log and the license banner (which shows part of the license owner's email), so the output stays clean during the viva. Every model is created inside this environment (`gp.Model(env=ENV)`).

### 3.2 The `RoutingModel` class

```python
RoutingModel(demand, blocks, hours, use_on_off=False,
             force_on_off=None, allow_unserved=False)
```

| Parameter | Meaning | Typical value |
|---|---|---|
| `demand` | `{region: [demand per block]}` | `data.DEMAND` |
| `blocks` | List of block names | `data.BLOCKS` |
| `hours` | Hours per block (converts $/hour into $/block) | `4` (or `24` for the daily average, `1` for one hour) |
| `use_on_off` | **`False` = Part 1 (LP)**, **`True` = Part 2 (IP)** | |
| `force_on_off` | Fix some ON/OFF decisions, e.g. `{"Mumbai": False}` | Used for outages and testing plans |
| `allow_unserved` | Allow demand to go unserved (with a big penalty) instead of the model becoming infeasible | Used for testing plans and in the demo |

**How one class does both parts:** the only difference between Part 1 and Part 2 is whether `on[dc]` is the number `1` (always ON) or a binary variable that Gurobi decides. Everything else is shared.

### 3.3 What `solve()` does, step by step

**Step A: create decision variables**

```python
x[dc, r, b] = m.addVar(lb=0)       # only if route_allowed(dc, r)
```
- `x[dc, region, block]` = thousand queries/hour sent from a data center to a region in a block. Continuous and ≥ 0.
- **Prohibited routes get no variable at all**, so the model cannot use them. This is cleaner than the classroom "Big-M cost" trick.
- 13 allowed routes × 6 blocks = **78 variables**.

```python
on[dc] = m.addVar(vtype=GRB.BINARY)   # Part 2
on[dc] = 1                            # Part 1
```
- In Part 2, `on[dc]` is **binary** (0 or 1). That is what makes it Integer Programming.
- If a data center appears in `force_on_off`, its binary is fixed by setting `LB = UB = 0` or `1`.

```python
unserved[r, b] = m.addVar(lb=0)  if allow_unserved else 0
```
- An optional "safety valve" variable used only when testing a plan or in the demo.

**Step B: add constraints**

```python
# Supply: a data center cannot send more than its capacity (0 if OFF)
sum over regions x[dc, r, b]  <=  CAPACITY[dc] * on[dc]

# Demand: every region's demand must be met
sum over dcs x[dc, r, b] + unserved[r, b]  ==  demand[r][b]
```
- 4 data centers × 6 blocks = **24 supply constraints**.
- 5 regions × 6 blocks = **30 demand constraints**.
- The `* on[dc]` on the right of the supply constraint is the key link: if `on = 0`, capacity becomes 0 and nothing can be sent.

**Step C: set the objective (minimise)**

```python
routing_cost = hours * Σ cost(dc, r) * x[dc, r, b]
fixed_cost   = Σ FIXED_COST[dc] * on[dc]
penalty      = 100 * hours * Σ unserved          # $100 per 1000 lost queries
minimise  routing_cost + fixed_cost + penalty
```
- The penalty of $100 per 1000 queries is roughly **50–100× the normal cost of serving them**, so the model only leaves demand unserved when it is truly impossible to serve it.

**Step D: read the results** (stored as attributes on the object)

| Attribute | Meaning |
|---|---|
| `optimal` | `True` if Gurobi found the optimal solution |
| `routing_cost` | $ spent on serving queries (for the horizon) |
| `fixed_cost` | $ spent on keeping data centers ON |
| `total_cost` | `routing_cost + fixed_cost` (the penalty is **not** included, so this is the real money spent) |
| `is_on` | `{dc: True/False}` |
| `flow` | `{(dc, region, block): amount}` for every route actually used |
| `unserved` | `{(region, block): amount}` of lost demand (empty if all served) |
| `total_unserved` | Total lost queries over the day (thousands) |

**Helper methods**
- `load(dc, block)`: total queries a data center handles in one block (used for utilization %).
- `on_list()`: names of the data centers that are ON.

---

## 4. `vam.py`: Vogel's Approximation Method

**Purpose:** implements the **hand method taught in class** for finding a good starting solution of a transportation problem. We use it on **one time block** (the busiest one, 20-24 IST) to compare it with Gurobi's true optimum.

### Function

```python
vogel(cost, supply, demand)  →  (allocation, total_cost)
```

| Input | Format |
|---|---|
| `cost` | `{(source, destination): cost}`. A missing pair means a prohibited route |
| `supply` | `{source: capacity}` |
| `demand` | `{destination: demand}` |

### What it does, step by step
1. **Balancing.** If total supply > total demand, it adds a **"Dummy" destination** that absorbs the extra supply at cost 0 (exactly as in class). For block 20-24: supply 720 − demand 505 = **dummy of 215**.
2. **Prohibited routes** get a cost of `BIG_M = 1000` so VAM never chooses them (the classroom Big-M trick).
3. **Loop** until all rows or columns are used up:
   - For every remaining row and column, compute the **penalty** = difference between its two smallest costs (`penalty()` helper).
   - Pick the row or column with the **largest penalty**.
   - In it, pick the **cheapest cell**.
   - Allocate `min(remaining supply, remaining demand)` to that cell.
   - Remove the row (supply used up) and/or column (demand met).
4. Return the allocation and its total cost.

Result for 20-24: VAM cost = **$644.65/hour**, Gurobi optimum = **$621.40/hour**, so VAM is **3.74% worse**. A step-by-step trace is in [02_PROBLEM_AND_SOLUTION.md](02_PROBLEM_AND_SOLUTION.md#step-1-one-block-vam-vs-optimal).

---

## 5. `main.py`: the full study (the report program)

**Purpose:** runs the whole analysis in order and prints each result in readable tables, then draws the charts.

**Run it:**
```bash
conda activate opr
cd d:\OPR_project
python main.py
```

### Helpers at the top
- `line(title)`: prints a section header surrounded by `=====` lines.
- `print_plan(plan, block)`: prints a data center × region table for one block. It works for both Gurobi results (keys `(dc, region, block)`) and VAM results (keys `(dc, region)`).

### The five steps it prints

| Step | What it does | Key output |
|---|---|---|
| **STEP 0** | Prints the cost table with capacities; `-` marks prohibited routes | 4×5 cost table |
| **STEP 1** | Takes the busiest block (20-24). Shows supply 720 vs demand 505 (unbalanced, dummy 215). Runs **VAM**, then **Gurobi** on the same block, and compares | VAM $644.65 vs optimal $621.40 (VAM 3.74% worse) |
| **STEP 2** | **Part 1 (LP):** full day, all 4 data centers ON | Routing $11,696 + Fixed $14,000 = **$25,696/day** |
| **STEP 3** | **Part 2 (IP):** full day, the model chooses ON/OFF | Frankfurt **OFF**, total **$21,822/day**, saving **$3,874 (15.1%)**, plus a utilization table |
| **STEP 4** | Plans using only the **daily average** demand, then tests that ON/OFF decision against real block-by-block demand | Average plan keeps only Mumbai + Virginia ($18,035 on paper), but **876k queries/day go unserved** |
| **CHARTS** | Calls the 4 chart functions | 4 PNG files in `figures/` |

---

## 6. `charts.py`: report figures

**Purpose:** draws 4 simple, clean charts with matplotlib and saves them as PNG files (150 dpi) in `figures/`. The folder is created automatically.

| Item | What it is |
|---|---|
| `COLORS`, `REGION_COLOR` | One fixed colour per region (India blue, SE Asia orange, Middle East green, Europe yellow, USA pink), the same in every chart and in the demo |
| `clean(ax, title, xlabel, ylabel)` | Common styling: bold left title, no top/right border, light horizontal grid |
| `save(fig, name)` | Saves the figure into `figures/` and prints the path |
| `demand_chart()` | → `1_demand.png` |
| `cost_chart(plans)` | → `2_cost_comparison.png` |
| `utilization_chart(plan)` | → `3_utilization.png` |
| `unserved_chart(plan)` | → `4_static_plan_failure.png` |

Every figure is explained in detail in [04_FIGURES_GUIDE.md](04_FIGURES_GUIDE.md).

---

## 7. `demo.py`: the live interactive demo

**Purpose:** a pygame window that animates the optimal routing over a day and lets you change the situation live (mode, outages, demand). Every change re-solves the Gurobi model in milliseconds.

**Run it:**
```bash
conda activate opr
python demo.py
```

### Main parts of the file

| Part | What it does |
|---|---|
| Constants (`W`, `H`, `MAP_W`, colours) | Window 1200×700 px; the left 820 px is the map, the rest is the info panel |
| `BLOCK_SECONDS = 4` | Each 4-hour block is shown for 4 real seconds (a full day takes 24 s) |
| `REGION_COLOR` | The same region colours as the charts (slightly darker shades for the dark background) |
| `POSITION` | Rough (longitude, latitude) of every data center and region on the map |
| `MODE_NAME` | Text for the 3 modes |
| `to_screen(name)` | Converts longitude/latitude into pixel x/y |
| `curve_point(p0, p1, s)` | Point at fraction `s` along a curved (quadratic Bézier) path, used to draw the arcs and move the dots |
| `class Demo` | The application (see below) |

### `Demo` class methods

| Method | Job |
|---|---|
| `__init__` | Opens the window, loads fonts, calls `reset()` |
| `reset()` | Mode = IP, no outages, demand ×1.0, block 0, then solves |
| `demand()` | Current demand = `data.DEMAND` × multiplier |
| `solve()` | Builds and solves the right `RoutingModel` for the current mode, outages and demand, and measures the solve time in ms |
| `text(...)` | Small helper to draw text |
| `draw_map()` | Grid, curved flow lines, moving dots, region circles, data center squares, red "NOT served" warnings |
| `draw_timeline()` | Title, IST clock, the 6 demand bars at the top |
| `draw_panel()` | Right panel: mode, solve time, capacity bars, daily cost, unserved queries, controls |
| `handle(event)` | Keyboard and mouse controls |
| `run()` | Main loop at 60 frames/second: read input → advance clock → draw everything |

Everything you see and every control is explained in [03_DEMO_GUIDE.md](03_DEMO_GUIDE.md).

---

## 8. Supporting files

### `environment.yml`
```yaml
name: opr
dependencies:
  - python=3.11
  - matplotlib
  - pip
  - pip:
      - gurobipy
      - pygame
```
Recreate the exact environment on any computer with:
```bash
conda env create -f environment.yml
conda activate opr
```

### `.gitignore`
Tells git which files must **never** be uploaded to GitHub:
- `info.txt` (the assignment brief)
- `gurobi.lic` and `*.lic`: **the Gurobi license contains a secret key**
- `__pycache__/`, `.ipynb_checkpoints/` (Python's automatic cache files)

### Gurobi license (not in the project folder)
The academic license file is stored at `C:\Users\<you>\gurobi.lic`, **outside** the project, so it can never be uploaded by accident. Gurobi finds it there automatically. Do **not** show this file on screen or share it. If it ever leaks, revoke it in the Gurobi web license manager and create a new one.

### `figures/`
Output folder. It is recreated every time `main.py` runs.

---

## 9. How to change the scenario

All changes happen in **`data.py`** only. Then run `main.py` or `demo.py` again.

| Want to try… | Change |
|---|---|
| Cheaper Frankfurt | Lower `FIXED_COST["Frankfurt"]` or `SERVING_COST["Frankfurt"]` |
| A stricter SLA | Lower `MAX_LATENCY` (e.g. 100) and more routes become prohibited |
| Users care more about speed | Raise `LATENCY_PENALTY` |
| A bigger Mumbai | Raise `CAPACITY["Mumbai"]` |
| A new data center | Add it to `DATA_CENTERS`, `CAPACITY`, `SERVING_COST`, `FIXED_COST`, `LATENCY` (and `POSITION` in `demo.py`) |
