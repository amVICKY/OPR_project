"""Simple charts for the report (saved as PNG files in the 'figures' folder)."""
import os

import matplotlib.pyplot as plt

import data

os.makedirs("figures", exist_ok=True)

COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]   # one per region
REGION_COLOR = dict(zip(data.REGIONS, COLORS))


def clean(ax, title, xlabel, ylabel):
    ax.set_title(title, loc="left", fontweight="bold")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", color="#e4e3df")
    ax.set_axisbelow(True)


def save(fig, name):
    path = os.path.join("figures", name)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("  saved", path)


def demand_chart():
    """Demand of each region in each time block."""
    fig, ax = plt.subplots(figsize=(8, 4))
    for r in data.REGIONS:
        ax.plot(data.BLOCKS, data.DEMAND[r], marker="o", lw=2,
                color=REGION_COLOR[r], label=r)
    total = [sum(data.DEMAND[r][k] for r in data.REGIONS) for k in range(len(data.BLOCKS))]
    ax.plot(data.BLOCKS, total, ls="--", lw=2, color="#52514e", label="Total")
    clean(ax, "Demand moves with time zones", "Time block (IST)",
          "Queries (thousand / hour)")
    ax.legend(ncol=3, frameon=False, fontsize=8.5)
    save(fig, "1_demand.png")


def cost_chart(plans):
    """plans = {label: solved RoutingModel}.  Fixed + routing cost as stacked bars."""
    labels = list(plans)
    fixed = [p.fixed_cost for p in plans.values()]
    routing = [p.routing_cost for p in plans.values()]

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(labels, fixed, width=0.5, color="#a3a29c", label="Fixed cost (data centers ON)")
    ax.bar(labels, routing, width=0.5, bottom=fixed, color="#6250d6",
           label="Routing cost (serving queries)")
    for k, p in enumerate(plans.values()):
        ax.text(k, p.total_cost + 300, f"${p.total_cost:,.0f}", ha="center", fontweight="bold")
    clean(ax, "Daily cost: LP vs IP", "", "Cost per day ($)")
    ax.set_ylim(0, max(p.total_cost for p in plans.values()) * 1.2)
    ax.legend(frameon=False, fontsize=8.5)
    save(fig, "2_cost_comparison.png")


def utilization_chart(plan):
    """How full each data center is in each block (percent of capacity)."""
    table = [[100 * plan.load(dc, b) / data.CAPACITY[dc] for b in data.BLOCKS]
             for dc in data.DATA_CENTERS]

    fig, ax = plt.subplots(figsize=(8, 3.2))
    ax.imshow(table, cmap="Blues", vmin=0, vmax=100, aspect="auto")
    for i, dc in enumerate(data.DATA_CENTERS):
        for k in range(len(data.BLOCKS)):
            text = f"{table[i][k]:.0f}%" if plan.is_on[dc] else "OFF"
            ax.text(k, i, text, ha="center", va="center",
                    color="white" if table[i][k] > 55 else "black")
    ax.set_xticks(range(len(data.BLOCKS)), data.BLOCKS)
    ax.set_yticks(range(len(data.DATA_CENTERS)), data.DATA_CENTERS)
    ax.set_title("Capacity used by each data center (Part 2 plan)", loc="left", fontweight="bold")
    ax.set_xlabel("Time block (IST)")
    save(fig, "3_utilization.png")


def unserved_chart(plan):
    """Queries that could not be served in each block (stacked by region)."""
    fig, ax = plt.subplots(figsize=(8, 3.8))
    bottom = [0] * len(data.BLOCKS)
    for r in data.REGIONS:
        values = [plan.unserved.get((r, b), 0) for b in data.BLOCKS]
        if sum(values) == 0:
            continue
        ax.bar(data.BLOCKS, values, bottom=bottom, width=0.55, color=REGION_COLOR[r], label=r)
        bottom = [a + v for a, v in zip(bottom, values)]
    for k, v in enumerate(bottom):
        if v > 0:
            ax.text(k, v + 2, f"{v:.0f}", ha="center")
    clean(ax, "Average-demand plan fails at busy hours", "Time block (IST)",
          "Unserved queries (thousand / hour)")
    ax.set_ylim(0, max(bottom) * 1.25 + 1)
    ax.legend(frameon=False, fontsize=8.5)
    save(fig, "4_static_plan_failure.png")
