import sys, paramiko

HOST = "194.87.140.199"
PORT = 2222
USER = "root"
PASS = "z-L#WF19WwXgh*"

CMDS = [
    ("git pull", "cd /var/www/ai-manager/repo && git pull --ff-only"),
    ("restart", "systemctl restart ai-manager"),
    ("status", "sleep 2 && systemctl is-active ai-manager"),
    ("health", "curl -s http://127.0.0.1:8000/api/health || curl -s http://127.0.0.1:8000/health"),
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
last = None
for attempt in range(1, 6):
    try:
        c.connect(HOST, port=PORT, username=USER, password=PASS, timeout=30, banner_timeout=30, auth_timeout=30)
        print("CONNECTED (attempt", attempt, ")")
        break
    except Exception as e:
        last = e
        print(f"attempt {attempt} fail: {e}")
        import time; time.sleep(3)
else:
    print("CONNECT_FAIL:", last); sys.exit(1)

for name, cmd in CMDS:
    stdin, stdout, stderr = c.exec_command(cmd, timeout=60)
    out = stdout.read().decode("utf-8", "replace").strip()
    err = stderr.read().decode("utf-8", "replace").strip()
    rc = stdout.channel.recv_exit_status()
    print(f"\n=== {name} (rc={rc}) ===")
    if out: print(out)
    if err: print("STDERR:", err)

c.close()
print("\nDONE")
