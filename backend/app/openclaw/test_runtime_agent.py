from backend.app.openclaw.runtime import (
    OpenClawRuntime,
    OpenClawRuntimeError,
)


def main() -> None:
    print("OPENCLAW RUNTIME AGENT TEST")
    print("===========================")

    runtime = OpenClawRuntime()

    print("Executable:", runtime.executable)
    print("Agent ID:", runtime.agent_id)

    print("\n1. Checking Gateway...")
    health = runtime.health_check()

    print("Gateway healthy:", health.get("healthy"))
    print("Gateway version:", health.get("gateway_version"))
    print("Gateway URL:", health.get("gateway_url"))
    print("Runtime status:", health.get("runtime_status"))

    if not health.get("healthy"):
        print("\nGATEWAY HEALTH CHECK FAILED")
        return

    print("\n2. Running OpenClaw agent...")

    try:
        result = runtime.run_agent(
            "Reply with exactly: OPENCLAW AGENT EXECUTION PASSED"
        )

        print("\nAgent execution returned successfully.")
        print("Response:")
        print(result)

        print("\nOPENCLAW RUNTIME AGENT TEST PASSED")

    except OpenClawRuntimeError as exc:
        print("\nOPENCLAW RUNTIME AGENT TEST FAILED")
        print("Error:", exc)


if __name__ == "__main__":
    main()