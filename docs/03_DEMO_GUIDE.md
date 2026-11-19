# 03 · Live Demo Guide (`demo.py`)

This guide explains **everything about the live demo**: how to start it, what every shape, colour, number and line on the screen means, every control, what happens inside the code when you press something, and a ready-made script for the viva.

> **Related guides**
> - [01_CODE_GUIDE.md](01_CODE_GUIDE.md): what every file contains
> - [02_PROBLEM_AND_SOLUTION.md](02_PROBLEM_AND_SOLUTION.md): the problem and the maths
> - [04_FIGURES_GUIDE.md](04_FIGURES_GUIDE.md): the charts

---

## 1. What the demo is for

The report (`main.py`) shows the answer as **tables and static charts**. The demo shows the **same model working live**:

- You **watch** queries flow from data centers to regions as the day passes.
- You **change the situation** (switch model, break a data center, raise demand) and **Gurobi solves the model again instantly**. The new optimal plan appears on screen within milliseconds.

This proves the result is not a hard-coded picture: it is a real optimisation model reacting to new input.

---

## 2. How to start it

```bash
conda activate opr
cd d:\OPR_project
python demo.py
```

A window of **1200 × 700 pixels** opens. Close it with **Esc** or the window's ✕ button.

**Requirements:** the `opr` conda environment (Python 3.11, `gurobipy`, `pygame`) and the Gurobi license at `C:\Users\<you>\gurobi.lic`. No GPU is needed. The demo runs on any laptop.

---

## 3. Screen layout

```
┌──────────────────────────────────────────────────────┬────────────────────────────┐
│  Live AI Query Routing     [▇] [▇] [▇] [▇] [▇] [█]    │  MODE                      │
│  21:30 IST                 00-04 ... 20-24 (timeline) │  Part 2: Integer Program   │
│                                                      │  Demand x1.0  solved in 5ms│
│        (USA)                (Europe)                 │                            │
│          ●                     ●                     │  DATA CENTERS              │
│           \                 /    \                   │  Mumbai     ██████████ 100%│
│          [■] Virginia   [□] Frankfurt  ●(Mid East)   │  Singapore  ██████     65% │
│                                     \     ●(India)   │  Frankfurt              OFF│
│                                    [■] Mumbai        │  Virginia   ██████████ 100%│
│                                           ●(SE Asia) │                            │
│                                     [■] Singapore    │  COST FOR THE DAY          │
│                                                      │  TOTAL $21,822             │
│                MAP  (left, 820 px)                   │  UNSERVED QUERIES          │
│                                                      │  CONTROLS ...              │
└──────────────────────────────────────────────────────┴────────────────────────────┘
```

- **Left (820 px): the map**, with the clock and timeline on top.
- **Right (380 px): the information panel.**

---

## 4. Everything on the screen, explained

### 4.1 Title and clock (top-left)

| Element | Meaning |
|---|---|
| **Live AI Query Routing** | Title |
| **`21:30 IST`** | The current simulated time of day in Indian Standard Time |
| **PAUSED** (red) | Appears when the clock is paused with Space |

**Speed:** each 4-hour block lasts **4 real seconds** (`BLOCK_SECONDS = 4`), so a whole day takes **24 seconds** and then loops back to midnight. The clock moves smoothly inside a block (e.g. 20:00 → 21:00 → 22:00 …).

### 4.2 Timeline bars (top)

- **6 bars, one per time block** (00-04, 04-08, 08-12, 12-16, 16-20, 20-24).
- **Bar height = total demand** of all regions in that block (height = total ÷ 9 pixels). The 20-24 bar is tallest because that block has the highest demand (505 k/h).
- **The blue bar is the block currently shown** on the map. The others are dark grey.
- Label underneath: *"total demand per block"*.
- If you change demand with ↑/↓, all bars grow or shrink.

### 4.3 The map background
- Faint grid lines every 30° of longitude and 20° of latitude: a **simple flat world map**. West (USA) is on the left, East (Asia) on the right.
- It is not a real map image. Positions are approximate longitude/latitude, enough to show "who is near whom".

### 4.4 Regions (circles), the users

| Feature | Meaning |
|---|---|
| **Circle** | A user region (India, Southeast Asia, Middle East, Europe, USA) |
| **Colour** | Fixed identity colour per region (India blue, SE Asia orange, Middle East green, Europe yellow, USA pink), the same as in the report charts |
| **Size** | **Grows with current demand** (radius = 8 + 2.2 × √demand). Watch India grow in the evening and the USA grow in the IST night |
| **Name + "131k/h"** | Region name and its demand right now (thousand queries/hour) |
| **Red ring + "X k/h NOT served"** | That region's demand **cannot be fully met** in this block (only happens with outages, demand spikes or the average plan) |

### 4.5 Data centers (squares), the GPUs

| Look | Status shown | Meaning |
|---|---|---|
| **White filled square** | **ON** (green text) | Running. The model decided to keep it |
| **Grey outlined square** | **OFF** (grey text) | **The optimisation model chose to switch it off** to save its fixed cost (e.g. Frankfurt in Part 2) |
| **Dark red square with red ✕** | **OUTAGE** (red text) | **You broke it** by clicking. The model must work without it |

### 4.6 Flows (curved lines + moving dots), the routing decision

| Feature | Meaning |
|---|---|
| **Curved line** from a square to a circle | That data center **serves** that region in the current block (the variable $x_{ijt} > 0$) |
| **Line thickness** | More queries = thicker (width = flow ÷ 12, at least 2 px) |
| **Moving dots** | Queries travelling to users. **More dots = more queries** (number = flow ÷ 10, at least 2). They always move from data center → region |
| **Dot colour** | The **destination region's** colour. Blue dots from Mumbai mean "Mumbai is answering Indian users" |
| **No line** | That route is not used now, or is **prohibited** (latency > 150 ms, e.g. Singapore → USA never appears) |

The curve shape is a quadratic Bézier curve that arcs upward, only to make the routes easy to tell apart.

**Lines change when the block changes** because the optimal routing is different in each block (e.g. at 00-04 Mumbai sends 56 k/h to Europe, at 16-20 it doesn't).

### 4.7 Right panel

**MODE**

| Text | Meaning |
|---|---|
| `Part 1: Transportation LP (all ON)` | Mode 1 |
| `Part 2: Integer Program (choose ON/OFF)` | Mode 2 (default) |
| `Plan made from AVERAGE demand` | Mode 3 |
| `Demand x1.0` | Current demand multiplier (changed with ↑/↓) |
| `solved in 5 ms by Gurobi` | How long the **last** Gurobi solve took, proof that it is solved live |

**DATA CENTERS (capacity used, *current block*)**

For each data center, a bar showing **load ÷ capacity** in the block on screen, plus the % value. *OFF* or *OUTAGE* is shown instead when it is not running.
Example (Part 2, 20-24): Mumbai 100%, Singapore 65%, Frankfurt OFF, Virginia 100%.

**COST FOR THE DAY** (always the **whole day**, all 6 blocks, not only the current block)

| Line | Meaning |
|---|---|
| Routing cost | $ spent serving queries: Σ cost × flow × 4 hours |
| Fixed cost | $ for data centers that are ON (OFF and OUTAGE sites cost $0) |
| **TOTAL** | Routing + fixed. The penalty for unserved queries is **not** included: this is the real money spent |

**UNSERVED QUERIES**

| Line | Meaning |
|---|---|
| This block | Lost demand in the block on screen (thousand/hour) |
| Whole day | Lost queries over the whole day (thousand) |
| **Green** | All demand served |
| **Red** | Some users are not served |

**CONTROLS**: a reminder of the keys (section 5).

---

## 5. Controls: everything you can do

| Key / action | What happens | Re-solves Gurobi? |
|---|---|---|
| **`1`** | Switch to **Part 1: LP**. All data centers forced ON | ✅ |
| **`2`** | Switch to **Part 2: IP**. The model chooses ON/OFF | ✅ |
| **`3`** | Switch to the **average-demand plan** (explained below) | ✅ |
| **Mouse click on a data center square** | Toggle **OUTAGE**. Click again to repair | ✅ |
| **`↑` (Up arrow)** | Demand **+10%** (×1.1, ×1.2, …) | ✅ |
| **`↓` (Down arrow)** | Demand **−10%** (minimum ×0.1) | ✅ |
| **`Space`** | Pause / resume the clock (dots keep moving) | ❌ |
| **`→` (Right arrow)** | Jump to the **next** time block | ❌ |
| **`←` (Left arrow)** | Jump to the **previous** time block | ❌ |
| **`R`** | Reset: Mode 2, no outages, demand ×1.0, back to 00:00 | ✅ |
| **`Esc`** | Quit | – |

**Important:** the clock moving through the day does **not** re-solve. The model is solved **once for the whole day (all 6 blocks together)** whenever you change something, and the clock just chooses which block's part of that solution to draw. This is correct because in Part 2 the ON/OFF decision is for the whole day.

---

## 6. What happens inside the code when you press a key

```
 key / click
     │
     ▼
 handle(event) ──► changes state:  mode / broken set / scale
     │
     ▼
 solve()
   1. demand = data.DEMAND × scale
   2. forced = {each broken data center: OFF}
   3. build RoutingModel according to mode:
        mode 1 → RoutingModel(..., force_on_off=forced, allow_unserved=True)
        mode 2 → RoutingModel(..., use_on_off=True, force_on_off=forced, allow_unserved=True)
        mode 3 → (a) solve IP on AVERAGE demand → ON/OFF decision
                 (b) solve again on real demand with that decision fixed
   4. plan = model.solve()          (Gurobi, a few milliseconds)
   5. remember solve time
     │
     ▼
 run() loop, 60 times per second:
   advance clock → draw_timeline() → draw_map() → draw_panel()
   (all drawing reads from self.plan)
```

**Why `allow_unserved=True` in the demo:** if you break too many data centers or raise demand a lot, there is simply not enough capacity. A strict model would be **infeasible** and have no answer. Instead, the demo lets demand go unserved at a very high penalty ($100 per 1000 queries vs about $1–2 to serve), so:
- in normal situations the model **always** serves everyone (serving is far cheaper than the penalty), and the results are identical to `main.py`;
- in impossible situations it shows **exactly how much and where** demand is lost (red rings), instead of crashing.

In OR terms this turns the demand constraints into **soft constraints with a penalty**.

---

## 7. The three modes in detail

### Mode 1: Part 1, Transportation LP (all ON)
- Every data center is forced ON (unless you broke it).
- Only routing is optimised.
- **Result (normal demand):** total **$25,696/day**. Frankfurt is white/ON but barely used: it only carries a little of Europe at night and late evening.
- **Message:** "Everything stays on, and we pay $4,000 a day for a site we hardly use."

### Mode 2: Part 2, Integer Programming (default)
- The model chooses ON/OFF (binary $y_i$) **and** the routing.
- **Result:** Frankfurt **OFF** (grey), total **$21,822/day**, 0 unserved.
- **Message:** "The binary variable lets the model switch off Frankfurt and save 15%."

### Mode 3: Average-demand plan
- Step (a): the IP is solved using only each region's **daily average** demand → it decides to keep only **Mumbai + Virginia**.
- Step (b): that ON/OFF decision is **fixed** and tested against the real demand of each block.
- **Result:** Singapore and Frankfurt grey, **red rings on Southeast Asia** (from 08-12 onward) and **Europe** (20-24), **876k queries lost per day**. Total shows **$16,919**.
- **Why the total looks lower:** the 876k lost queries are never served, so we don't pay to serve them. It is "cheaper" only because users are left without answers.
- **Message:** "Planning on averages fails at peak hours. That's why we model demand block by block."

---

## 8. Measured results for common situations

| Situation | How to get there | Data centers ON | Cost/day | Unserved/day |
|---|---|---|---|---|
| IP, normal | `R` | Mumbai, Singapore, Virginia | **$21,822** | 0 |
| LP, normal | `1` | All 4 | **$25,696** | 0 |
| Average plan | `3` | Mumbai, Virginia | $16,919 | **876k** |
| IP + Mumbai outage | `2`, click Mumbai | Singapore, Frankfurt, Virginia | $24,876 | 0 |
| IP + Virginia outage | `2`, click Virginia | Mumbai, Singapore, Frankfurt | $25,540 | **80k** (USA) |
| IP + Mumbai outage + demand ×1.3 | `2`, click Mumbai, ↑↑↑ | Singapore, Frankfurt, Virginia | $27,561 | **968k** |

**Outage examples explained:**
- **Mumbai outage:** Frankfurt immediately turns **ON** again, because it is now needed as backup for India and the Middle East (Frankfurt can reach both within 150 ms). The cost rises but everyone is still served. This shows that the ON/OFF decision is made by the optimiser, not by a fixed rule.
- **Virginia outage:** the USA can only be served by Virginia or Frankfurt. Frankfurt's 170 k/h is not enough when the USA needs 185 k/h (04-08), so **15 k/h** of USA users are lost there, plus **5 k/h** at 20-24 when Frankfurt must also help Europe. That gives (15 + 5) × 4 h = **80k per day** (red ring on the USA).

---

## 9. Suggested 1–2 minute viva demo script

| # | Do | Say |
|---|---|---|
| 1 | Start `python demo.py`, let a full day play (24 s) | "Each circle is a user region and its size is current demand. Watch it move with time zones: USA at night IST, India in the evening. Dots are queries flowing from the data centers." |
| 2 | Point at the panel | "This is the optimal integer-programming plan. Frankfurt is OFF and the cost is $21,822 a day." |
| 3 | Press `1` | "If we keep everything on, as in the plain transportation LP, the cost goes up to $25,696. Frankfurt is on but hardly used." |
| 4 | Press `3` | "If we plan using only average demand, the plan looks cheap but fails at peak hours. Southeast Asia and Europe have red rings: 876 thousand queries a day unserved." |
| 5 | Press `2`, then click **Mumbai** | "Now Mumbai has an outage. Gurobi re-solves in milliseconds and switches Frankfurt back on as backup, and everyone is still served." |
| 6 | Press `↑` 3 times | "And on a viral launch day with 30% more demand, the model shows exactly where we run out of capacity." |
| 7 | Press `R` | "Everything you saw comes from the same model as our report." |

**Tips:**
- Press **Space** to freeze a block while you explain it.
- Use **→** to jump straight to **20-24** (the busiest block).
- Have the window open **before** the viva starts. The first solve happens at start-up.

---

## 10. Honest limitations (say these if asked)

1. **The map is schematic.** Positions are approximate, not a real geographic map.
2. **Demand is a 6-block plan**, not live traffic. The animation just plays the planned day.
3. **Dots are a visual effect.** Their number and speed only illustrate volume. The real numbers are in the panel.
4. **Unserved demand is a penalty (soft constraint)** so the demo never crashes. With normal settings it is always 0.
