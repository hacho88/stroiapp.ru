import sys, paramiko

HOST, PORT, USER, PASS = "194.87.140.199", 2222, "root", "z-L#WF19WwXgh*"
cmd = sys.argv[1] if len(sys.argv) > 1 else "echo no-cmd"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, port=PORT, username=USER, password=PASS, timeout=30, banner_timeout=30, auth_timeout=30)
stdin, stdout, stderr = c.exec_command(cmd, timeout=90)
out = stdout.read().decode("utf-8", "replace")
err = stderr.read().decode("utf-8", "replace")
print(out, end="")
if err.strip():
    print("--- STDERR ---")
    print(err, end="")
c.close()
