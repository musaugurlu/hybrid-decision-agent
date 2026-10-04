"""
scripts/run_all_benchmarks.py - Runs all 19 queries and formats complete Markdown output for experiment_report.md
"""

from agent_service import AgentService
from token_tracker import TokenTracker

svc = AgentService()
# Warm up
_ = svc.run("warmup")

all_queries = [
    # Category 1: Direct / Short Queries (11)
    ("Short", "Tip Calculation", "Calculate 15% tip on a $120 dinner bill"),
    ("Short", "Weather Forecast", "Will it rain tomorrow in Seattle?"),
    ("Short", "HR Benefits Policy", "Please search our internal knowledge base for company parental leave policy"),
    ("Short", "Package Delivery Tracking", "Where is my package for order #ORD-98214?"),
    ("Short", "Flight Status Check", "Has United Airlines flight UA412 landed yet?"),
    ("Short", "Currency Conversion", "How much is 250 Euros in US Dollars today?"),
    ("Short", "Inventory Stock Availability", "Do we have MacBook Pro 16 inch in Chicago warehouse?"),
    ("Short", "CRM Customer Profile", "Can you look up customer record for john.doe@example.com?"),
    ("Short", "Refund Transaction", "Please refund $45 for order #ORD-1234 because item was broken"),
    ("Short", "Send Email Notification", "Send email to sarah@acme.com letting her know contract is signed"),
    ("Short", "General Chit-Chat", "Hello, how are you doing today?"),

    # Category 2: Complex / Long Enterprise Queries (8)
    ("Complex", "Damaged Delivery Refund Claim", "Hi team, I am writing to you regarding order #ORD-98412 placed on September 28th. I received the package yesterday afternoon, but upon unboxing the delivered shipment, the glass display was completely shattered and unusable. I spoke with your phone representative Sarah earlier, who advised me to reach out here. Given the product arrived damaged through no fault of my own, I would like to request an immediate full refund of $189.50 back to my Visa credit card ending in 4102. Please confirm once the credit has been processed."),
    ("Complex", "Flight Delay Logistics", "Urgent assistance needed: Our executive leadership delegation is currently transiting through Chicago O'Hare for the annual tech summit. One of our key keynote speakers is scheduled on flight UA412 coming in from San Francisco. Due to adverse weather reported over the Midwest, our ground chauffeur team needs to know if UA412 has experienced any gate changes or landing delays, and what specific arrival terminal and baggage carousel they should proceed to."),
    ("Complex", "Treasury Multi-Currency Invoice", "Our European supply chain vendor just sent an invoice of 48,500 EUR for raw manufacturing materials, with a 3% early-payment discount applicable if settled within 10 days. Before our Treasury department initiates the wire transfer from our US operating bank account, we need to know the current market exchange rate and exactly how much this 48,500 EUR payment translates to in US Dollars."),
    ("Complex", "Q4 Stock Allocation", "We are preparing for the upcoming Q4 enterprise sales push and several regional distributors are asking for large allocations of the MacBook Pro 16 inch M3 units. Before we accept these non-refundable purchase orders, can you check the current available stock across our central fulfillment facilities, specifically Chicago, and verify if there are any pending restock shipments scheduled to arrive this month?"),
    ("Complex", "VIP CTO CRM Escalation", "We just received an urgent inbound ticket from an individual claiming to be the Chief Technology Officer at Nexus Global. His email is listed as john.doe@example.com. Before I jump on a live Zoom call with him to address his concerns, could you pull up his full CRM account record, subscription tier, total lifetime spend, and identify who their assigned enterprise account manager is?"),
    ("Complex", "Team Dinner Bill Split", "We just finished a team dinner with 8 colleagues at a downtown restaurant. The food subtotal was $432.50, and we need to calculate an 18% gratuity on that amount. Could you calculate what 18% tip on $432.50 is so we can finalize our expense report?"),
    ("Complex", "HR Policy Search", "Good morning HR team. My spouse and I are expecting our second child in November. Could you search our company knowledge base to verify the exact paid parental leave policy duration and whether it can be taken in split blocks across the year?"),
    ("Complex", "Strategic Arch Discussion", "Good afternoon! I have been reflecting on our quarterly agent architecture reviews. We have been looking at how microservices communicate, whether we need dedicated API gateways, how cost optimization plays into production deployments, and how teams coordinate across frontend and backend. Just wanted to say hello and see what your thoughts are on general software engineering best practices for building scalable distributed systems.")
]

runs = []
for cat, title, q in all_queries:
    res = svc.run(q)
    runs.append((cat, title, q, res))

# Print markdown table
print("TABLE_START")
print("| # | Query Scenario | Type | Target Tool | Laya Decision (Conf) | LLM Decision | Agreed | Baseline Tokens | Laya Tokens | Tokens Saved (%) | Baseline Latency | Laya Latency | Speedup |")
print("|:---|:---|:---:|:---|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|")

for i, (cat, title, q, res) in enumerate(runs, 1):
    label = res.tool_executed or "None"
    l_tool = res.laya_decision.selected_tool or "none"
    conf_val = res.laya_decision.confidence * 100
    llm_tool = res.llm_tool_chosen or "none"
    agreed = "✅ Yes" if res.tool_agreement else "⚠️ Diff"
    b_tok = f"{res.baseline_usage.total_tokens:,}"
    l_tok = f"{res.laya_usage.total_tokens:,}"
    saved = f"-{res.tokens_saved:,} ({res.savings_percentage:.1f}%)"
    b_lat = f"{res.baseline_latency.total_ms:.1f} ms"
    l_lat = f"{res.laya_latency.total_ms:.1f} ms"
    speedup = f"{res.speedup_factor:.2f}x"
    print(f"| {i} | **{title}** | {cat} | `{label}` | `{l_tool}` ({conf_val:.1f}%) | `{llm_tool}` | {agreed} | {b_tok} | {l_tok} | **{saved}** | {b_lat} | {l_lat} | **{speedup}** |")

print("TABLE_END")

# Aggregate Stats
total_q = len(runs)
total_base_tokens = sum(r[3].baseline_usage.total_tokens for r in runs)
total_laya_tokens = sum(r[3].laya_usage.total_tokens for r in runs)
total_saved_tokens = sum(r[3].tokens_saved for r in runs)
avg_saved_pct = (total_saved_tokens / total_base_tokens) * 100.0

total_agreed = sum(1 for r in runs if r[3].tool_agreement)
agreement_pct = (total_agreed / total_q) * 100.0

avg_base_lat = sum(r[3].baseline_latency.total_ms for r in runs) / total_q
avg_laya_lat = sum(r[3].laya_latency.total_ms for r in runs) / total_q
avg_speedup = avg_base_lat / avg_laya_lat

avg_base_routing = sum(r[3].baseline_latency.routing_ms for r in runs) / total_q
avg_laya_routing = sum(r[3].laya_latency.routing_ms for r in runs) / total_q
avg_routing_speedup = avg_base_routing / avg_laya_routing

total_cost_saved = sum(r[3].cost_saved_usd for r in runs)

print("STATS_START")
print(f"Total Queries: {total_q}")
print(f"Total Baseline Tokens: {total_base_tokens:,}")
print(f"Total Laya Tokens: {total_laya_tokens:,}")
print(f"Total Tokens Saved: {total_saved_tokens:,} ({avg_saved_pct:.1f}% reduction)")
print(f"Routing Agreement: {total_agreed}/{total_q} ({agreement_pct:.1f}%)")
print(f"Avg Total Latency: Baseline {avg_base_lat:.1f} ms vs Laya {avg_laya_lat:.1f} ms ({avg_speedup:.2f}x speedup)")
print(f"Avg Routing Time: Baseline {avg_base_routing:.1f} ms vs Laya {avg_laya_routing:.1f} ms ({avg_routing_speedup:.1f}x speedup)")
print(f"Total Cost Saved: ${total_cost_saved:.6f} USD")
print("STATS_END")
