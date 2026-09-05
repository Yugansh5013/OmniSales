import subprocess
import sys

commands = [
    ["docker", "cp", "shared/.", "omnisales-mcp-crm:/app/shared/"],
    ["docker", "cp", "mcp-servers/crm/server.py", "omnisales-mcp-crm:/app/server.py"],

    ["docker", "cp", "shared/.", "omnisales-orchestrator:/app/shared/"],
    ["docker", "cp", "agents/orchestrator/scanner.py", "omnisales-orchestrator:/app/agents/orchestrator/scanner.py"],
    ["docker", "cp", "agents/orchestrator/main.py", "omnisales-orchestrator:/app/agents/orchestrator/main.py"],

    ["docker", "cp", "shared/.", "omnisales-closer:/app/shared/"],
    ["docker", "cp", "agents/closer/skills.py", "omnisales-closer:/app/agents/closer/skills.py"],
    ["docker", "cp", "agents/closer/nodes.py", "omnisales-closer:/app/agents/closer/nodes.py"],
    ["docker", "cp", "agents/closer/graph.py", "omnisales-closer:/app/agents/closer/graph.py"],
    ["docker", "cp", "agents/closer/main.py", "omnisales-closer:/app/agents/closer/main.py"],

    ["docker", "cp", "shared/.", "omnisales-prospector:/app/shared/"],
    ["docker", "cp", "agents/prospector/skills.py", "omnisales-prospector:/app/agents/prospector/skills.py"],
    ["docker", "cp", "agents/prospector/nodes.py", "omnisales-prospector:/app/agents/prospector/nodes.py"],
    ["docker", "cp", "agents/prospector/main.py", "omnisales-prospector:/app/agents/prospector/main.py"],

    ["docker", "cp", "shared/.", "omnisales-guardian:/app/shared/"],
    ["docker", "cp", "agents/guardian/nodes.py", "omnisales-guardian:/app/agents/guardian/nodes.py"],
    ["docker", "cp", "agents/guardian/main.py", "omnisales-guardian:/app/agents/guardian/main.py"],

    ["docker", "cp", "shared/.", "omnisales-api-gateway:/app/shared/"],
    ["docker", "cp", "api-gateway/main.py", "omnisales-api-gateway:/app/api-gateway/main.py"],
]

for cmd in commands:
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"Error copying {' '.join(cmd)}: {r.stderr}")
    else:
        print(f"Copied: {' '.join(cmd[1:3])} -> {cmd[3]}")

print("Restarting containers...")
restart_cmd = ["docker", "restart", "omnisales-mcp-crm", "omnisales-orchestrator", "omnisales-closer", "omnisales-prospector", "omnisales-guardian", "omnisales-api-gateway"]
r = subprocess.run(restart_cmd, capture_output=True, text=True)
print("Restart result:", r.stdout)
