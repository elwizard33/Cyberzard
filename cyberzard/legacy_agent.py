from __future__ import annotations

from typing import Dict, Any, List, Callable

from .agent_engine.config import SYSTEM_PROMPT
from .agent_engine.tools import read_file, scan_server, propose_remediation

ToolFunc = Callable[..., Dict[str, Any]]

TOOL_REGISTRY: Dict[str, ToolFunc] = {
    "read_file": read_file,
    "scan_server": scan_server,
    "propose_remediation": propose_remediation,
}


class MiniReasoner:
    def __init__(self, max_steps: int = 5):
        self.max_steps = max_steps

    def _select_tools(self, query: str):
        q = query.lower().strip()
        if any(k in q for k in ["scan", "malware", "miner", "ioc", "infection"]):
            return [{"name": "scan_server", "args": {"include_encrypted": True}}]
        if q.startswith("read "):
            path = query.split(" ", 1)[1].strip()
            return [{"name": "read_file", "args": {"path": path}}]
        return []

    def run(self, query: str) -> Dict[str, Any]:
        plan = self._select_tools(query)
        outputs = []
        for idx, spec in enumerate(plan):
            if idx >= self.max_steps:
                break
            fn = TOOL_REGISTRY.get(spec["name"])  # type: ignore[arg-type]
            if not fn:
                outputs.append({"tool": spec["name"], "error": "unknown_tool"})
                continue
            try:
                result = fn(**spec.get("args", {}))  # type: ignore[arg-type]
            except Exception as e:  # pragma: no cover
                result = {"success": False, "error": str(e)}
            outputs.append({"tool": spec["name"], "result": result})
        return {"plan": plan, "tool_outputs": outputs}


def run_agent(provider: str = "local-mini", user_query: str = "", max_steps: int = 5) -> Dict[str, Any]:
    reasoner = MiniReasoner(max_steps=max_steps)
    reasoning_bundle = reasoner.run(user_query)
    remediation_plan = None
    for out in reasoning_bundle["tool_outputs"]:
        if out.get("tool") == "scan_server" and out.get("result", {}).get("success"):
            remediation_plan = propose_remediation(out["result"])  # type: ignore[arg-type]
            break
    return {
        "provider": provider,
        "query": user_query,
        "status": "completed",
        "system_prompt_excerpt": SYSTEM_PROMPT.splitlines()[0],
        "reasoning": reasoning_bundle,
        "remediation_plan": remediation_plan,
        "final": "Success – minimal local reasoning path complete.",
    }

__all__ = ["run_agent", "SYSTEM_PROMPT"]
