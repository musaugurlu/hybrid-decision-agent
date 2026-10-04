"""
scripts/generate_report_table.py - Generates formatted markdown tables for docs/experiment_report.md
"""

from token_tracker import TokenTracker

tracker = TokenTracker.get_instance()
runs = tracker.history[-19:]

lines = []
lines.append("| # | Query Scenario | Type | Target Tool | Laya Decision (Conf) | LLM Decision | Agreed | Baseline Tokens | Laya Tokens | Tokens Saved (%) | Baseline Latency | Laya Latency | Speedup |")
lines.append("|:---|:---|:---:|:---|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|")

for i, r in enumerate(runs, 1):
    q = r["query"]
    label = r.get("tool_executed") or "None"
    words = len(q.split())
    q_type = "Complex" if words > 30 else "Short"
    short_title = q[:44] + ("..." if len(q) > 44 else "")
    l_tool = r["laya_tool"] or "none"
    conf_val = r["laya_confidence"] * 100
    l_conf = f"{conf_val:.1f}%"
    llm_tool = r["llm_tool"] or "none"
    agreed = "✅ Yes" if r["tool_agreement"] else "⚠️ Diff"
    base_tok = f"{r['baseline_usage']['total_tokens']:,}"
    laya_tok = f"{r['laya_usage']['total_tokens']:,}"
    saved = f"-{r['tokens_saved']:,} ({r['savings_percentage']:.1f}%)"
    base_lat = f"{r['baseline_latency']['total_ms']:.1f} ms"
    laya_lat = f"{r['laya_latency']['total_ms']:.1f} ms"
    speedup = f"{r['speedup_factor']:.2f}x"
    lines.append(
        f"| {i} | {short_title} | {q_type} | `{label}` | `{l_tool}` ({l_conf}) | `{llm_tool}` | {agreed} | {base_tok} | {laya_tok} | **{saved}** | {base_lat} | {laya_lat} | **{speedup}** |"
    )

print("\n".join(lines))
