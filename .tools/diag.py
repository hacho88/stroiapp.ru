import paramiko

HOST, PORT, USER, PASS = "194.87.140.199", 2222, "root", "z-L#WF19WwXgh*"
BACKEND = "/var/www/ai-manager/repo/backend"

REMOTE_TEST = r'''
import asyncio, json, sys
sys.path.insert(0, "/var/www/ai-manager/repo/backend")
from app.services.deepseek_client import deepseek_client
from app.api.routes.ui_builder import clean_ai_json, normalize_elements, SYSTEM_PROMPT

async def main():
    print("api_key set:", bool(deepseek_client.api_key), "len:", len(deepseek_client.api_key or ""))
    raw = await deepseek_client.chat(
        prompt="Сделай карточку товара: цемент М500, цена 320 руб/мешок, кнопка В корзину",
        model="deepseek-chat", max_tokens=2048, temperature=0.4, system=SYSTEM_PROMPT)
    print("=== RAW (first 1500) ===")
    print(repr(raw[:1500]))
    data = clean_ai_json(raw)
    print("=== clean_ai_json type ===", type(data).__name__)
    els = normalize_elements(data)
    print("=== elements count ===", len(els))
    if els: print(json.dumps(els[0], ensure_ascii=False)[:400])

asyncio.run(main())
'''

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, port=PORT, username=USER, password=PASS, timeout=30, banner_timeout=30, auth_timeout=30)

sftp = c.open_sftp()
with sftp.file("/tmp/diag_uibuilder.py", "w") as f:
    f.write(REMOTE_TEST)
sftp.close()
print("uploaded test")

cmd = f"cd {BACKEND} && nohup .venv/bin/python /tmp/diag_uibuilder.py > /tmp/diag_out.txt 2>&1 & echo LAUNCHED pid $!"
stdin, stdout, stderr = c.exec_command(cmd, timeout=20)
print(stdout.read().decode("utf-8", "replace"))
c.close()
