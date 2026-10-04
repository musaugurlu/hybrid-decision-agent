# ⚡ Decision Model (Laya) × Gemini Flash Experiment

An experimental AI Agent architecture testing **Decision Models (Laya / Jev)** in front of **Google Gemini Flash 8B** to eliminate token bloat and accelerate tool-assisted agent workflows.

---

### 🎯 The Question & The Experiment
> *"Can a non-autoregressive 'System 1' decision model placed in front of an LLM save token usage and pick tools accurately?"*

In standard LLM tool calling:
- **10 Tools = ~1,500 prompt tokens** attached to **every turn of every query**.
- When multi-turn reasoning executes, those tool schemas are re-billed repeatedly!

With **Laya Decision Model**:
- Laya executes in **~35ms on Apple Silicon Metal with 0 LLM API tokens**.
- If no tool is needed: Gemini receives **0 tool schemas** (95% token reduction).
- If a tool is needed: Gemini receives **only that 1 selected tool schema** (85-90% token reduction).

---

### 🛠️ 10 Available Experimental Tools
1. **`calculator`**: Safe arithmetic expressions, percentages, multiplications.
2. **`get_weather`**: City forecasts, temperature, precipitation.
3. **`search_knowledge_base`**: HR parental leave, vacation policy, IT guides.
4. **`check_order_status`**: Shipping tracking, courier, delivery status.
5. **`check_flight_status`**: Flight arrival/departure times, gate info, delays.
6. **`convert_currency`**: Live FX exchange conversions (USD, EUR, GBP, JPY).
7. **`check_inventory_stock`**: Warehouse quantities, SKU availability, restock.
8. **`lookup_customer_crm`**: Customer profiles, tier level, lifetime value.
9. **`refund_transaction`**: Payment refunds, reasons, confirmation IDs.
10. **`send_email_notification`**: Automated email dispatching and confirmations.

---

### 🧪 Getting Started
1. Click any of the quick-action buttons below or type any custom query.
2. Observe the **Laya Decision step** (selected tool, calibrated confidence, probabilities).
3. Review the **Performance & Token Usage Comparison Card** comparing Baseline vs Laya.
4. Open the settings icon (top right) to toggle between **Dual Benchmark**, **With Laya**, or **Without Laya**.
