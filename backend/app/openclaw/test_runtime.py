from backend.app.openclaw.runtime import OpenClawRuntime


runtime = OpenClawRuntime()

health = runtime.health_check()

print("OPENCLAW HEALTH CHECK")
print("=====================")
print("Healthy:", health["healthy"])
print("RPC OK:", health["rpc_ok"])
print("Gateway Version:", health["gateway_version"])
print("Gateway URL:", health["gateway_url"])
print("Runtime Status:", health["runtime_status"])
print("Capability:", health["capability"])

assert health["rpc_ok"] is True
assert health["runtime_status"] == "running"

print()
print("OPENCLAW RUNTIME TEST PASSED")