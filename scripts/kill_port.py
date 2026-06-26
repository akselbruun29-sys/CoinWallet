import subprocess
import re

out = subprocess.check_output("netstat -ano", text=True)
pids = set()
for line in out.splitlines():
    if ":8000" in line and "LISTENING" in line:
        m = re.search(r"(\d+)\s*$", line.strip())
        if m:
            pids.add(int(m.group(1)))

print("PIDs on 8000:", pids)
for pid in pids:
    try:
        subprocess.run(["taskkill", "/PID", str(pid), "/F", "/T"], check=False)
        print("killed", pid)
    except Exception as e:
        print("failed", pid, e)
