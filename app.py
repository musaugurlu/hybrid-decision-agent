"""
app.py - Chainlit UI for the Laya Decision Model vs Gemini Flash Experiment.
Demonstrates token savings, latency improvements, and tool-routing accuracy
by placing Laya ('System 1' Decision Model) in front of Google Gemini Flash 8B.
"""

import os
import chainlit as cl
from chainlit.input_widget import Select, TextInput

from agent_service import AgentService, ExecutionResult
from token_tracker import TokenTracker

# Initialize services
agent_service = AgentService()
tracker = TokenTracker.get_instance()


def build_comparison_markdown(result: ExecutionResult, cumulative: dict) -> str:
    """Formats a rich markdown card displaying side-by-side metrics and response times."""
    base = result.baseline_usage
    laya = result.laya_usage
    b_lat = result.baseline_latency
    l_lat = result.laya_latency

    agreement_badge = "✅ **Aligned** (Both chose same tool)" if result.tool_agreement else "⚠️ **Diverged** (Laya vs LLM differed)"
    api_badge = "🟢 **Live Google Gemini API**" if result.is_live_api else "🔵 **Gemini Token & Latency Simulator** (Set GEMINI_API_KEY for live calls)"

    laya_tool_display = f"`{result.laya_decision.selected_tool}`" if result.laya_decision and result.laya_decision.selected_tool else "*None (Direct Answer)*"
    llm_tool_display = f"`{result.llm_tool_chosen}`" if result.llm_tool_chosen else "*None (Direct Answer)*"

    conf_pct = round((result.laya_decision.confidence if result.laya_decision else 0.0) * 100, 1)

    table = f"""
### ⚖️ Performance & Response Time Benchmark

{api_badge}

| Metric | Without Laya (Baseline LLM) | With Laya (Decision Router) | Efficiency Gain |
| :--- | :--- | :--- | :--- |
| **Tools Bound in Prompt** | **10 Tools** (All Schemas) | **{ '1 Tool' if result.tool_executed else '0 Tools' }** | 📉 **{ '-90%' if result.tool_executed else '-100%' } schemas** |
| **Tool Selection** | {llm_tool_display} | {laya_tool_display} *(conf: {conf_pct}%)* | {agreement_badge} |
| **Prompt (Input) Tokens** | `{base.prompt_tokens:,}` | `{laya.prompt_tokens:,}` | 🟢 **-{base.prompt_tokens - laya.prompt_tokens:,} tokens** |
| **Completion (Output) Tokens** | `{base.completion_tokens:,}` | `{laya.completion_tokens:,}` | `{base.completion_tokens - laya.completion_tokens:+,} tokens` |
| **Total Tokens Billed** | `{base.total_tokens:,}` | `{laya.total_tokens:,}` | 🚀 **-{result.tokens_saved:,} tokens ({result.savings_percentage}%)** |
| **Estimated Cost (USD)** | `${result.baseline_cost_usd:.6f}` | `${result.laya_cost_usd:.6f}` | 💰 **-${result.cost_saved_usd:.6f}** |
| **Tool Routing Latency** | `{b_lat.routing_ms:.1f} ms` (Remote LLM API) | `{l_lat.routing_ms:.1f} ms` (Local Laya MLX) | ⚡ **{result.routing_speedup_factor:.1f}x faster routing** |
| **Tool Execution Duration**| `{b_lat.tool_exec_ms:.2f} ms` | `{l_lat.tool_exec_ms:.2f} ms` | — |
| **Synthesis Duration** | `{b_lat.synthesis_ms:.1f} ms` | `{l_lat.synthesis_ms:.1f} ms` | ⚡ Faster prefill on 1 tool |
| **Total Response Time** | **`{b_lat.total_ms:.1f} ms`** | **`{l_lat.total_ms:.1f} ms`** | ⏱️ **{result.speedup_factor:.2f}x faster ({result.latency_saved_ms:+.1f} ms saved)** |

---

#### 📈 Cumulative Session Statistics ({cumulative.get('total_queries', 0)} queries)
- **Token Efficiency:** Saved **`{cumulative.get('total_tokens_saved', 0):,}`** tokens (**{cumulative.get('average_savings_pct', 0.0)}% average reduction**)
- **Average Response Time:** Baseline `{cumulative.get('avg_baseline_latency_ms', 0.0):.1f} ms` vs Laya `{cumulative.get('avg_laya_latency_ms', 0.0):.1f} ms` (**{cumulative.get('avg_speedup_factor', 1.0):.2f}x average speedup**, -`{cumulative.get('avg_latency_saved_ms', 0.0):.1f} ms`)
- **Average Routing Speedup:** ⚡ **{cumulative.get('avg_routing_speedup_factor', 1.0):.1f}x faster tool decisions** via local Apple Silicon MLX
- **Routing Agreement Rate:** `{cumulative.get('agreement_rate_pct', 0.0)}%`
- **Total Estimated Cost Saved:** `${cumulative.get('total_cost_saved_usd', 0.0):.5f} USD`
"""
    return table


async def display_starter_actions():
    """Renders quick-action starter buttons for both short and complex enterprise queries."""
    complex_actions = [
        cl.Action(
            name="quick_query",
            payload={"query": "Hi team, I am writing to you regarding order #ORD-98412 placed on September 28th. I received the package yesterday afternoon, but upon unboxing the delivered shipment, the glass display was completely shattered and unusable. I spoke with your phone representative Sarah earlier, who advised me to reach out here. Given the product arrived damaged through no fault of my own, I would like to request an immediate full refund of $189.50 back to my Visa credit card ending in 4102. Please confirm once the credit has been processed."},
            label="🏢 Complex Refund Claim (88 words)",
        ),
        cl.Action(
            name="quick_query",
            payload={"query": "Good morning HR team. My spouse and I are expecting our second child in November. Could you search our company knowledge base to verify the exact paid parental leave policy duration and whether it can be taken in split blocks across the year?"},
            label="🏢 HR Policy Search (43 words)",
        ),
        cl.Action(
            name="quick_query",
            payload={"query": "Urgent assistance needed: Our executive leadership delegation is currently transiting through Chicago O'Hare for the annual tech summit. One of our key keynote speakers is scheduled on flight UA412 coming in from San Francisco. Due to adverse weather reported over the Midwest, our ground chauffeur team needs to know if UA412 has experienced any gate changes or landing delays, and what specific arrival terminal and baggage carousel they should proceed to."},
            label="🏢 Flight Delay Logistics (71 words)",
        ),
        cl.Action(
            name="quick_query",
            payload={"query": "Our European supply chain vendor just sent an invoice of 48,500 EUR for raw manufacturing materials, with a 3% early-payment discount applicable if settled within 10 days. Before our Treasury department initiates the wire transfer from our US operating bank account, we need to know the current market exchange rate and exactly how much this 48,500 EUR payment translates to in US Dollars."},
            label="🏢 Treasury FX Invoice (63 words)",
        ),
        cl.Action(
            name="quick_query",
            payload={"query": "We are preparing for the upcoming Q4 enterprise sales push and several regional distributors are asking for large allocations of the MacBook Pro 16 inch M3 units. Before we accept these non-refundable purchase orders, can you check the current available stock across our central fulfillment facilities, specifically Chicago, and verify if there are any pending restock shipments scheduled to arrive this month?"},
            label="🏢 Q4 Stock Allocation (62 words)",
        ),
        cl.Action(
            name="quick_query",
            payload={"query": "We just received an urgent inbound ticket from an individual claiming to be the Chief Technology Officer at Nexus Global. His email is listed as john.doe@example.com. Before I jump on a live Zoom call with him to address his concerns, could you pull up his full CRM account record, subscription tier, total lifetime spend, and identify who their assigned enterprise account manager is?"},
            label="🏢 VIP CTO CRM Lookup (63 words)",
        ),
        cl.Action(
            name="quick_query",
            payload={"query": "Good afternoon! I have been reflecting on our quarterly agent architecture reviews. We have been looking at how microservices communicate, whether we need dedicated API gateways, how cost optimization plays into production deployments, and how teams coordinate across frontend and backend. Just wanted to say hello and see what your thoughts are on general software engineering best practices for building scalable distributed systems."},
            label="🏢 Strategic Chat - No Tool (63 words)",
        ),
        cl.Action(name="quick_query", payload={"query": "Calculate 15% tip on a $120 dinner bill"}, label="⚡ Quick Tip"),
        cl.Action(name="quick_query", payload={"query": "Will it rain tomorrow in Seattle?"}, label="⚡ Quick Weather"),
        cl.Action(name="quick_query", payload={"query": "Where is package #ORD-98214?"}, label="⚡ Quick Order"),
        cl.Action(name="show_stats", payload={}, label="📊 View All Session Stats"),
    ]
    await cl.Message(
        content="💡 **Select an experimental scenario below (including complex multi-sentence enterprise prompts) or type your own:**",
        actions=complex_actions,
    ).send()


@cl.on_chat_start
async def on_chat_start():
    # Setup interactive chat settings
    settings = await cl.ChatSettings(
        [
            Select(
                id="mode",
                label="Routing Mode",
                values=["dual_benchmark", "with_laya", "without_laya"],
                initial_index=0,
                description="dual_benchmark: Compare both side-by-side | with_laya: Laya Decision Model | without_laya: Standard 10-tool LLM",
            ),
            Select(
                id="model",
                label="Gemini Flash Model",
                values=["gemini-1.5-flash-8b", "gemini-1.5-flash", "gemini-2.0-flash"],
                initial_index=0,
                description="Target Gemini model",
            ),
        ]
    ).send()

    cl.user_session.set("settings", settings)

    api_configured = agent_service.is_api_key_configured()
    status_msg = (
        "🟢 **Live Google Gemini API key detected.** Running real API calls with token tracking."
        if api_configured
        else "ℹ️ **No GEMINI_API_KEY detected in .env.** Running high-fidelity Gemini Flash Token Simulator with exact schema token counting. Add `GEMINI_API_KEY=your_key` in `.env` to enable live Gemini API calls."
    )

    welcome_content = f"""
# 🚀 Laya Decision Model × Gemini Flash Agent Experiment

Welcome! This experimental platform tests whether placing **Laya** (a lightweight 'System 1' non-autoregressive decision model) in front of **Google Gemini Flash 8B** can save massive token overhead and accelerate agent responsiveness.

### 🔬 The Core Hypothesis:
- **Baseline (Without Laya):** In standard tool calling, **all 10 tool schemas** (~1,500 prompt tokens) must be attached to *every single prompt*. Multi-turn execution sends these schemas repeatedly!
- **With Laya Decision Model:** Laya processes the user prompt locally on Apple Silicon Metal in a single forward pass (**~35ms, 0 Gemini API tokens**). It routes to either:
  1. **No tool needed:** Gemini is invoked with **0 tools bound** (*95% token savings!*).
  2. **Specific tool:** Gemini is invoked with **ONLY the 1 selected tool bound** (*80-90% token savings!*).

{status_msg}
"""
    await cl.Message(content=welcome_content).send()
    await display_starter_actions()


@cl.on_settings_update
async def on_settings_update(settings: dict):
    cl.user_session.set("settings", settings)
    mode = settings.get("mode", "dual_benchmark")
    model = settings.get("model", "gemini-1.5-flash-8b")
    await cl.Message(
        content=f"⚙️ **Settings Updated:** Mode = `{mode}`, Model = `{model}`"
    ).send()


async def process_user_query(query_text: str):
    """Core handler that runs the experiment, displays step-by-step progress, and renders comparison."""
    settings = cl.user_session.get("settings") or {}
    mode = settings.get("mode", "dual_benchmark")
    model_name = settings.get("model", "gemini-1.5-flash-8b")

    # Step 1: Laya Decision Model
    async with cl.Step(name="🧠 Laya Decision Model (Apple Silicon MLX)", type="tool") as step1:
        step1.input = f"Evaluating intent & tool criteria for: '{query_text}'"
        result = await agent_service.run_async(query=query_text, mode=mode, model_name=model_name)
        dec = result.laya_decision

        if dec:
            choice_str = f"**Selected:** `{dec.raw_choice}`"
            conf_str = f"**Confidence:** `{dec.confidence * 100:.1f}%`"
            lat_str = f"**Forward Pass Latency:** `{dec.latency_ms:.2f} ms`"
            tokens_str = "**LLM API Tokens Billed:** `0 tokens` (runs 100% locally on device)"

            top_3 = "\n".join([f"- `{alt['tool']}`: {alt['probability'] * 100:.2f}%" for alt in dec.top_alternatives])
            step1.output = f"{choice_str} | {conf_str} | {lat_str}\n{tokens_str}\n\n**Top Alternatives:**\n{top_3}"
        else:
            step1.output = "Decision model bypassed or inactive."

    # Step 2: Tool Execution (if tool was selected)
    if result.tool_executed:
        async with cl.Step(name=f"⚙️ Tool Execution: `{result.tool_executed}`", type="tool") as step2:
            step2.input = f"Arguments: {result.tool_args}"
            step2.output = result.tool_output or "Tool executed with no output."

    # Step 3: LLM Response Message
    response_msg = cl.Message(content=result.final_response)
    await response_msg.send()

    # Step 4: Comparative Analysis Card
    cum_stats = tracker.get_cumulative_stats()
    comparison_md = build_comparison_markdown(result, cum_stats)

    await cl.Message(content=comparison_md).send()
    await display_starter_actions()


@cl.action_callback("quick_query")
async def on_quick_query(action: cl.Action):
    query = action.payload.get("query", "")
    await cl.Message(content=f"👉 *Query:* **{query}**", author="User").send()
    await process_user_query(query)


@cl.action_callback("show_stats")
async def on_show_stats(action: cl.Action):
    stats = tracker.get_cumulative_stats()
    content = f"""
### 📊 Cumulative Experiment Analytics

- **Total Logged Queries:** `{stats['total_queries']}`
- **Baseline LLM Tokens (All Tools):** `{stats['total_baseline_tokens']:,}`
- **Laya-Routed Tokens:** `{stats['total_laya_tokens']:,}`
- **Total Tokens Saved:** 🏆 `{stats['total_tokens_saved']:,}`
- **Average Token Savings:** 🚀 **{stats['average_savings_pct']}%**
- **Average Response Time:** Baseline `{stats['avg_baseline_latency_ms']:.1f} ms` vs Laya `{stats['avg_laya_latency_ms']:.1f} ms` (**{stats['avg_speedup_factor']:.2f}x speedup**, `{stats['avg_latency_saved_ms']:.1f} ms saved)
- **Average Tool Routing Speedup:** ⚡ **{stats['avg_routing_speedup_factor']:.1f}x faster** via local Laya MLX
- **Decision Agreement Rate:** `{stats['agreement_rate_pct']}%` (Laya vs Gemini Flash)
- **Net Cost Saved:** `${stats['total_cost_saved_usd']:.5f} USD`
"""
    await cl.Message(content=content).send()
    await display_starter_actions()


@cl.on_message
async def on_message(message: cl.Message):
    await process_user_query(message.content)
