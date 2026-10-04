"""
token_tracker.py - Records, analyzes, and persists token usage, cost comparisons, and response times.
Stores experiment history to a JSON file and maintains session-wide aggregate metrics.
"""

import json
import os
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path


DATA_DIR = Path(__file__).parent / "data"
HISTORY_FILE = DATA_DIR / "token_usage_history.json"


@dataclass
class TokenBreakdown:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

    @property
    def cost_usd(self) -> float:
        """Calculates estimated cost based on Gemini 1.5 Flash-8B pricing:
        $0.0375 / 1M prompt tokens, $0.15 / 1M completion tokens."""
        prompt_cost = (self.prompt_tokens / 1_000_000.0) * 0.0375
        completion_cost = (self.completion_tokens / 1_000_000.0) * 0.1500
        return prompt_cost + completion_cost


@dataclass
class RouteLatencyBreakdown:
    routing_ms: float       # Time to decide tool (Laya MLX forward pass vs LLM Round 1 routing)
    tool_exec_ms: float     # Execution duration of Python tool
    synthesis_ms: float     # Final response synthesis (Round 2 completion)
    total_ms: float         # End-to-end total response time


@dataclass
class ExperimentRecord:
    id: str
    timestamp: str
    query: str
    mode: str
    model: str
    laya_tool: Optional[str]
    laya_confidence: float
    laya_latency_ms: float
    llm_tool: Optional[str]
    llm_latency_ms: float
    tool_agreement: bool
    baseline_usage: TokenBreakdown
    laya_usage: TokenBreakdown
    tokens_saved: int
    savings_percentage: float
    baseline_cost_usd: float
    laya_cost_usd: float
    cost_saved_usd: float
    baseline_latency: RouteLatencyBreakdown
    laya_latency: RouteLatencyBreakdown
    latency_saved_ms: float
    speedup_factor: float
    routing_speedup_factor: float
    tool_executed: Optional[str] = None
    tool_output: Optional[str] = None
    response_text: str = ""


class TokenTracker:
    """Manages recording and persistence of token metrics and response times."""

    _instance: Optional["TokenTracker"] = None

    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.history: List[Dict[str, Any]] = self._load_history()

    def _load_history(self) -> List[Dict[str, Any]]:
        if HISTORY_FILE.exists():
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save_history(self):
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            print(f"[TokenTracker] Error saving history: {e}")

    @classmethod
    def get_instance(cls) -> "TokenTracker":
        if cls._instance is None:
            cls._instance = TokenTracker()
        return cls._instance

    def record_experiment(self, record: ExperimentRecord) -> Dict[str, Any]:
        data = asdict(record)
        self.history.append(data)
        self._save_history()
        return data

    def get_cumulative_stats(self) -> Dict[str, Any]:
        """Calculates cumulative statistics across all logged experiments."""
        if not self.history:
            return {
                "total_queries": 0,
                "total_baseline_tokens": 0,
                "total_laya_tokens": 0,
                "total_tokens_saved": 0,
                "average_savings_pct": 0.0,
                "agreement_rate_pct": 0.0,
                "total_cost_saved_usd": 0.0,
                "avg_baseline_latency_ms": 0.0,
                "avg_laya_latency_ms": 0.0,
                "avg_latency_saved_ms": 0.0,
                "avg_speedup_factor": 1.0,
                "avg_routing_speedup_factor": 1.0,
            }

        total_queries = len(self.history)
        total_baseline = sum(r["baseline_usage"]["total_tokens"] for r in self.history)
        total_laya = sum(r["laya_usage"]["total_tokens"] for r in self.history)
        total_saved = sum(r["tokens_saved"] for r in self.history)
        total_agreed = sum(1 for r in self.history if r["tool_agreement"])

        avg_pct = (
            ((total_baseline - total_laya) / total_baseline * 100.0)
            if total_baseline > 0
            else 0.0
        )
        agreement_pct = (total_agreed / total_queries * 100.0) if total_queries > 0 else 0.0
        total_cost_saved = sum(r.get("cost_saved_usd", 0.0) for r in self.history)

        # Latency calculations
        base_latencies = [
            r.get("baseline_latency", {}).get("total_ms", r.get("llm_latency_ms", 0.0))
            for r in self.history
        ]
        laya_latencies = [
            r.get("laya_latency", {}).get("total_ms", r.get("laya_latency_ms", 0.0))
            for r in self.history
        ]

        avg_base_lat = sum(base_latencies) / total_queries if total_queries > 0 else 0.0
        avg_laya_lat = sum(laya_latencies) / total_queries if total_queries > 0 else 0.0
        avg_saved_lat = max(0.0, avg_base_lat - avg_laya_lat)
        avg_speedup = (avg_base_lat / max(1.0, avg_laya_lat)) if avg_laya_lat > 0 else 1.0

        # Routing phase speedup
        base_routings = [
            r.get("baseline_latency", {}).get("routing_ms", r.get("llm_latency_ms", 0.0))
            for r in self.history
        ]
        laya_routings = [
            r.get("laya_latency", {}).get("routing_ms", r.get("laya_latency_ms", 0.0))
            for r in self.history
        ]
        avg_base_routing = sum(base_routings) / total_queries if total_queries > 0 else 0.0
        avg_laya_routing = sum(laya_routings) / total_queries if total_queries > 0 else 0.0
        avg_routing_speedup = (avg_base_routing / max(1.0, avg_laya_routing)) if avg_laya_routing > 0 else 1.0

        return {
            "total_queries": total_queries,
            "total_baseline_tokens": total_baseline,
            "total_laya_tokens": total_laya,
            "total_tokens_saved": total_saved,
            "average_savings_pct": round(avg_pct, 1),
            "agreement_rate_pct": round(agreement_pct, 1),
            "total_cost_saved_usd": round(total_cost_saved, 6),
            "avg_baseline_latency_ms": round(avg_base_lat, 1),
            "avg_laya_latency_ms": round(avg_laya_lat, 1),
            "avg_latency_saved_ms": round(avg_saved_lat, 1),
            "avg_speedup_factor": round(avg_speedup, 2),
            "avg_routing_speedup_factor": round(avg_routing_speedup, 1),
        }
