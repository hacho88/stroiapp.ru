import paramiko

HOST, PORT, USER, PASS = "194.87.140.199", 2222, "root", "z-L#WF19WwXgh*"
BACKEND = "/var/www/ai-manager/repo/backend"

REMOTE = r'''
import asyncio, sys, traceback, httpx, os
sys.path.insert(0, "/var/www/ai-manager/repo/backend")
os.chdir("/var/www/ai-manager/repo/backend")
from app.core.config import settings

async def main():
    key = settings.deepseek_api_key
    print("key len:", len(key or ""), "prefix:", (key or "")[:6])
    # direct minimal call with short timeout + full traceback
    try:
        async with httpx.AsyncClient(timeout=30.0) as cl:
            r = await cl.post("https://api.deepseek.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={"model":"deepseek-chat","messages":[{"role":"user","content":"Say OK"}],"max_tokens":10})
            print("HTTP", r.status_code)
            print("BODY", r.text[:600])
    except Exception as e:
        print("EXC TYPE:", type(e).__name__)
        print("EXC REPR:", repr(e))
        traceback.print_exc()

asyncio.run(main())
print("=== TEST DONE ===")
'''

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, port=PORT, username=USER, password=PASS, timeout=30, banner_timeout=30, auth_timeout=30)
sftp = c.open_sftp()
with sftp.file("/tmp/ds_test.py", "w") as f:
    f.write(REMOTE)
sftp.close()
# run with unbuffered output, wait up to 60s
stdin, stdout, stderr = c.exec_command(f"cd {BACKEND} && .venv/bin/python -u /tmp/ds_test.py", timeout=70)
print(stdout.read().decode("utf-8", "replace"))
err = stderr.read().decode("utf-8", "replace")
if err.strip():
    print("STDERR:", err)
c.close()
