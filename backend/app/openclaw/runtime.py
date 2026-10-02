import json
import os
import subprocess
from typing import Any, Dict, Optional


class OpenClawRuntimeError(RuntimeError):
    """Raised when an OpenClaw runtime invocation fails."""


class OpenClawRuntime:
    """
    Integration adapter between the Python application and the
    OpenClaw Gateway-backed agent runtime.

    OpenClaw CLI calls are executed through the installed CLI.
    Gateway-backed execution is the default behavior of `openclaw agent`.
    """

    def __init__(
        self,
        executable: Optional[str] = None,
        agent_id: Optional[str] = None,
        timeout: int = 600,
    ) -> None:
        self.executable = executable or os.getenv(
            "OPENCLAW_EXECUTABLE",
            "openclaw.cmd",
        )
        self.agent_id = agent_id or os.getenv(
            "OPENCLAW_AGENT_ID",
            "main",
        )
        self.timeout = timeout

    def health_check(self) -> Dict[str, Any]:
        """Verify that the OpenClaw CLI and Gateway are reachable."""

        command = [
            self.executable,
            "gateway",
            "status",
            "--json",
        ]

        result = self._run(command)

        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise OpenClawRuntimeError(
                "OpenClaw returned invalid JSON from gateway status."
            ) from exc

        rpc = payload.get("rpc", {})
        gateway = payload.get("gateway", {})
        runtime = payload.get("service", {}).get("runtime", {})

        return {
            "healthy": bool(rpc.get("ok")),
            "rpc_ok": bool(rpc.get("ok")),
            "gateway_version": gateway.get("version"),
            "gateway_url": rpc.get("url"),
            "runtime_status": runtime.get("status"),
            "capability": rpc.get("capability"),
        }

    def run_agent(
        self,
        message: str,
        *,
        session_key: Optional[str] = None,
        model: Optional[str] = None,
        thinking: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute one agent turn through the OpenClaw Gateway.
        """

        if not message or not message.strip():
            raise ValueError("OpenClaw message cannot be empty.")

        command = [
            self.executable,
            "agent",
            "--agent",
            self.agent_id,
            "--message",
            message,
            "--json",
        ]

        if session_key:
            command.extend(["--session-key", session_key])

        if model:
            command.extend(["--model", model])

        if thinking:
            command.extend(["--thinking", thinking])

        result = self._run(command)

        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise OpenClawRuntimeError(
                "OpenClaw returned invalid JSON from agent execution."
            ) from exc

        if not payload.get("ok", False):
            error = payload.get("error", {})
            raise OpenClawRuntimeError(
                error.get("message", "OpenClaw agent execution failed.")
            )

        return payload

    def _run(self, command: list[str]) -> subprocess.CompletedProcess[str]:
        """Execute an OpenClaw CLI command safely."""

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False,
            )
        except FileNotFoundError as exc:
            raise OpenClawRuntimeError(
                f"OpenClaw executable not found: {self.executable}"
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise OpenClawRuntimeError(
                "OpenClaw runtime request timed out."
            ) from exc

        if result.returncode != 0:
            error_text = result.stderr.strip() or result.stdout.strip()

            raise OpenClawRuntimeError(
                f"OpenClaw command failed with exit code "
                f"{result.returncode}: {error_text}"
            )

        return result