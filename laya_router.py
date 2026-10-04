"""
laya_router.py - Integration with Laya Decision Model using laya-mlx.
Laya is a non-autoregressive 'System 1' decision model that performs typed choices
in a single fast forward pass (typically 20-50ms) on Apple Silicon Metal.
It replaces expensive LLM tool-routing overhead and uses 0 LLM API tokens.
"""

import time
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import warnings

# Suppress temperature clamping warning from laya_mlx for cleaner terminal output
warnings.filterwarnings("ignore", message=".*laya-mlx: this checkpoint ships temperatures outside.*")

from tools import LAYA_TOOL_CRITERIA, TOOLS_BY_NAME


@dataclass
class LayaDecision:
    raw_choice: str
    selected_tool: Optional[str]
    confidence: float
    answer_confidence: float
    probabilities: Dict[str, float]
    latency_ms: float
    input_tokens: int
    model_name: str = "convaiinnovations/laya"
    top_alternatives: list = field(default_factory=list)

    @property
    def is_tool_needed(self) -> bool:
        return self.selected_tool is not None and self.selected_tool in TOOLS_BY_NAME


class LayaRouter:
    """Manages the in-memory Laya MLX decision model instance."""

    _instance: Optional["LayaRouter"] = None

    def __init__(self, model_name: str = "english"):
        self.model_name = model_name
        self.agent = None
        self._initialize_model()

    def _initialize_model(self):
        """Loads the Laya MLX agent into memory."""
        try:
            from laya_mlx import Router
            router = Router()
            self.agent = router.load(self.model_name)
        except Exception as e:
            print(f"[LayaRouter] Warning loading MLX model: {e}")
            self.agent = None

    @classmethod
    def get_instance(cls) -> "LayaRouter":
        if cls._instance is None:
            cls._instance = LayaRouter()
        return cls._instance

    def route_query(self, user_query: str) -> LayaDecision:
        """Evaluates user query through Laya decision model in a single forward pass."""
        questions = {
            "tool_decision": {
                "type": "choice",
                "instructions": "Which tool is required to fulfill this user request?",
                "criteria": LAYA_TOOL_CRITERIA,
            }
        }

        t0 = time.perf_counter()
        if self.agent is not None:
            res = self.agent.system_one(user_query, questions)
            t1 = time.perf_counter()
            latency_ms = round((t1 - t0) * 1000.0, 2)

            ans = res["answers"]["tool_decision"]
            raw_choice = ans.get("choice", "none")
            confidence = ans.get("confidence", 0.0)
            ans_conf = ans.get("answer_confidence", confidence)
            raw_probs = ans.get("probabilities", {})

            # Sort probabilities descending
            sorted_probs = dict(sorted(raw_probs.items(), key=lambda kv: kv[1], reverse=True))

            # Top 3 alternatives excluding the winner
            top_alts = [
                {"tool": k, "probability": v}
                for k, v in sorted_probs.items()
                if k != raw_choice
            ][:3]

            input_tokens = res.get("usage", {}).get("input_tokens", len(user_query.split()) * 2)

            selected_tool = raw_choice if raw_choice != "none" and raw_choice in TOOLS_BY_NAME else None

            return LayaDecision(
                raw_choice=raw_choice,
                selected_tool=selected_tool,
                confidence=round(confidence, 4),
                answer_confidence=round(ans_conf, 4),
                probabilities=sorted_probs,
                latency_ms=latency_ms,
                input_tokens=input_tokens,
                model_name="convaiinnovations/laya (MLX Apple Silicon)",
                top_alternatives=top_alts,
            )
        else:
            # Fallback heuristic if MLX model failed to load
            latency_ms = 1.0
            return LayaDecision(
                raw_choice="none",
                selected_tool=None,
                confidence=0.5,
                answer_confidence=0.5,
                probabilities={"none": 1.0},
                latency_ms=latency_ms,
                input_tokens=len(user_query.split()),
                model_name="heuristic_fallback",
            )
