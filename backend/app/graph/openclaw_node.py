from typing import Any, Dict

from backend.app.openclaw.runtime import (
    OpenClawRuntime,
    OpenClawRuntimeError,
)
from backend.app.schemas.agent_state import AgentState


runtime = OpenClawRuntime()


def openclaw_node(state: AgentState) -> Dict[str, Any]:
    """
    Connect the LangGraph workflow to the OpenClaw runtime.

    The Gateway is treated as an external runtime capability.
    Provider/model authentication failures are recorded in state
    instead of crashing the complete workflow.
    """

    trace = list(state.get("trace", []))

    try:
        health = runtime.health_check()

        trace.append(
            {
                "agent": "openclaw_runtime",
                "action": "gateway_health_check",
                "status": "success",
                "gateway_version": health.get("gateway_version"),
                "gateway_url": health.get("gateway_url"),
                "runtime_status": health.get("runtime_status"),
                "capability": health.get("capability"),
            }
        )

        return {
            "current_agent": "openclaw_runtime",
            "current_stage": "openclaw",
            "observation": {
                "openclaw": {
                    "available": True,
                    "gateway": health,
                }
            },
            "trace": trace,
        }

    except OpenClawRuntimeError as exc:
        trace.append(
            {
                "agent": "openclaw_runtime",
                "action": "gateway_health_check",
                "status": "failed",
                "error": str(exc),
            }
        )

        return {
            "current_agent": "openclaw_runtime",
            "current_stage": "openclaw",
            "observation": {
                "openclaw": {
                    "available": False,
                    "error": str(exc),
                }
            },
            "errors": list(state.get("errors", [])) + [str(exc)],
            "last_error": str(exc),
            "trace": trace,
        }