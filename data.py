"""
All input data for the problem.

Units:
    queries -> thousand queries per hour
    money   -> US dollars ($)
    time    -> the day is split into 6 blocks of 4 hours (IST)
"""

# ---------------- Sources: GPU data centers ----------------
DATA_CENTERS = ["Mumbai", "Singapore", "Frankfurt", "Virginia"]

CAPACITY = {          # max queries it can answer (thousand / hour)
    "Mumbai": 200,
    "Singapore": 130,
    "Frankfurt": 170,
    "Virginia": 220,
}

SERVING_COST = {      # GPU + electricity cost, $ per 1000 queries
    "Mumbai": 1.10,
    "Singapore": 1.40,
    "Frankfurt": 1.50,
    "Virginia": 0.90,
}

FIXED_COST = {        # cost of keeping the data center ON for one day ($)
    "Mumbai": 3000,
    "Singapore": 3500,
    "Frankfurt": 4000,
    "Virginia": 3500,
}

# ---------------- Destinations: user regions ----------------
REGIONS = ["India", "Southeast Asia", "Middle East", "Europe", "USA"]

# ---------------- Time blocks ----------------
BLOCKS = ["00-04", "04-08", "08-12", "12-16", "16-20", "20-24"]   # IST
HOURS_PER_BLOCK = 4

# Demand of each region in each block (thousand queries / hour).
# Each region is busiest in its own local evening, so the peaks
# move with time zones (e.g. USA is busy when India is asleep).
DEMAND = {
    #                  00-04 04-08 08-12 12-16 16-20 20-24
    "India":          [41,   41,   107,  120,  139,  131],
    "Southeast Asia": [16,   46,   71,   75,   89,   51],
    "Middle East":    [29,   11,   34,   48,   51,   59],
    "Europe":         [119,  44,   31,   87,   104,  117],
    "USA":            [157,  185,  124,  36,   86,   147],
}

# ---------------- Latency (network delay) in milliseconds ----------------
LATENCY = {
    #             India  SE Asia  Mid East  Europe  USA
    "Mumbai":    [20,    60,      40,       120,    200],
    "Singapore": [60,    15,      90,       160,    220],
    "Frankfurt": [120,   160,     80,       15,     90],
    "Virginia":  [200,   220,     170,      85,     20],
}

MAX_LATENCY = 150        # SLA: a route slower than this is NOT allowed
LATENCY_PENALTY = 0.005  # $ per millisecond, per 1000 queries


# ---------------- Helper functions ----------------
def latency(dc, region):
    return LATENCY[dc][REGIONS.index(region)]


def route_allowed(dc, region):
    """A data center may serve a region only if latency is within the SLA."""
    return latency(dc, region) <= MAX_LATENCY


def cost(dc, region):
    """Cost of serving 1000 queries:  serving cost + latency penalty."""
    return round(SERVING_COST[dc] + LATENCY_PENALTY * latency(dc, region), 3)


def demand_of_block(block):
    """Demand of every region in one time block, e.g. demand_of_block('20-24')."""
    k = BLOCKS.index(block)
    return {r: DEMAND[r][k] for r in REGIONS}


def average_demand():
    """Static view: one number per region = average over the whole day."""
    return {r: [sum(DEMAND[r]) / len(BLOCKS)] for r in REGIONS}
