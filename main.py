"""
AI query routing across GPU data centers
Transportation Problem (LP) + Integer Programming, solved with Gurobi.

Run:  python main.py
"""
import charts
import data
from model import RoutingModel
from vam import vogel


def line(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def print_plan(plan, block):
    """Print the routing table (data center x region) for one block."""
    print(f"{'':12}" + "".join(f"{r:>15}" for r in data.REGIONS))
    for dc in data.DATA_CENTERS:
        row = [plan.get((dc, r, block), plan.get((dc, r), 0)) for r in data.REGIONS]
        print(f"{dc:12}" + "".join(f"{v:15.1f}" for v in row))


# ---------------------------------------------------------------- Step 0
line("STEP 0: Cost table ($ per 1000 queries)   '-' = not allowed (latency > SLA)")
print(f"{'':12}" + "".join(f"{r:>15}" for r in data.REGIONS) + f"{'Capacity':>12}")
for dc in data.DATA_CENTERS:
    cells = [f"{data.cost(dc, r):15.3f}" if data.route_allowed(dc, r) else f"{'-':>15}"
             for r in data.REGIONS]
    print(f"{dc:12}" + "".join(cells) + f"{data.CAPACITY[dc]:12}")


# ---------------------------------------------------------------- Step 1
PEAK = "20-24"
line(f"STEP 1: One block ({PEAK} IST) - VAM (hand method) vs Gurobi optimum")
demand = data.demand_of_block(PEAK)
supply = data.CAPACITY
print(f"Total supply = {sum(supply.values())},  total demand = {sum(demand.values())}"
      f"  -> unbalanced, add a Dummy column of {sum(supply.values()) - sum(demand.values())}")

cost_table = {(dc, r): data.cost(dc, r) for dc in data.DATA_CENTERS for r in data.REGIONS
              if data.route_allowed(dc, r)}
vam_plan, vam_cost = vogel(cost_table, supply, demand)
print("\nVAM allocation (thousand queries / hour):")
print_plan(vam_plan, PEAK)

one_block = RoutingModel({r: [demand[r]] for r in data.REGIONS}, [PEAK], hours=1).solve()
print("\nGurobi optimal allocation:")
print_plan(one_block.flow, PEAK)
print(f"\nVAM cost     = ${vam_cost:,.2f} per hour")
print(f"Optimal cost = ${one_block.routing_cost:,.2f} per hour")
print(f"VAM is {100 * (vam_cost / one_block.routing_cost - 1):.2f}% above the optimum")


# ---------------------------------------------------------------- Step 2
line("STEP 2: Part 1 - Transportation LP for the whole day (all data centers ON)")
lp = RoutingModel(data.DEMAND, data.BLOCKS, data.HOURS_PER_BLOCK).solve()
print(f"Routing cost = ${lp.routing_cost:,.0f}")
print(f"Fixed cost   = ${lp.fixed_cost:,.0f}   (all 4 ON)")
print(f"TOTAL        = ${lp.total_cost:,.0f} per day")


# ---------------------------------------------------------------- Step 3
line("STEP 3: Part 2 - Integer Programming (choose which data centers stay ON)")
ip = RoutingModel(data.DEMAND, data.BLOCKS, data.HOURS_PER_BLOCK, use_on_off=True).solve()
print("Decision:", ", ".join(f"{dc}={'ON' if on else 'OFF'}" for dc, on in ip.is_on.items()))
print(f"Routing cost = ${ip.routing_cost:,.0f}")
print(f"Fixed cost   = ${ip.fixed_cost:,.0f}")
print(f"TOTAL        = ${ip.total_cost:,.0f} per day")
saving = lp.total_cost - ip.total_cost
print(f"Saving vs Part 1 = ${saving:,.0f} per day ({100 * saving / lp.total_cost:.1f}%)")
print("\nUsed capacity (%) per block:")
print(f"{'':12}" + "".join(f"{b:>9}" for b in data.BLOCKS))
for dc in data.DATA_CENTERS:
    print(f"{dc:12}" + "".join(f"{100 * ip.load(dc, b) / data.CAPACITY[dc]:9.0f}"
                               for b in data.BLOCKS))


# ---------------------------------------------------------------- Step 4
line("STEP 4: Why dynamic demand matters - plan using only the DAILY AVERAGE")
static = RoutingModel(data.average_demand(), ["avg"], hours=24, use_on_off=True).solve()
print("Average-demand plan keeps ON:", ", ".join(static.on_list()))
print(f"Its cost on paper = ${static.total_cost:,.0f} per day (looks cheaper!)")

# Now test that ON/OFF decision against the real block-by-block demand
test = RoutingModel(data.DEMAND, data.BLOCKS, data.HOURS_PER_BLOCK,
                    force_on_off=static.is_on, allow_unserved=True).solve()
print(f"But with real demand, {test.total_unserved:,.0f} thousand queries per day "
      f"can NOT be served:")
for (r, b), v in sorted(test.unserved.items(), key=lambda item: item[0][1]):
    print(f"   {b}  {r:15} {v:6.1f} thousand / hour")
print("-> The dynamic (block-by-block) model is needed to keep enough capacity at peaks.")


# ---------------------------------------------------------------- Charts
line("CHARTS")
charts.demand_chart()
charts.cost_chart({"Part 1: LP\n(all ON)": lp, "Part 2: IP\n(optimal ON/OFF)": ip})
charts.utilization_chart(ip)
charts.unserved_chart(test)
