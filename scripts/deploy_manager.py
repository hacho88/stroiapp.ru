import requests, json, os

OPENCART_URL = 'https://stroiapp.ru'
TOKEN = 'change_this_ai_manager_token'

files = {
    'catalog/view/theme/unishop2/manager/index.html': 'D:/Projects/ai.stroiapp.ru/ai.stroiapp.ru/frontend/opencart-manager/index.html',
    'catalog/view/theme/unishop2/manager/app.js': 'D:/Projects/ai.stroiapp.ru/ai.stroiapp.ru/frontend/opencart-manager/app.js',
    'catalog/view/theme/unishop2/manager/designer.js': 'D:/Projects/ai.stroiapp.ru/ai.stroiapp.ru/frontend/opencart-manager/designer.js',
}

url = f'{OPENCART_URL}/index.php?route=api/ai_manager&action=file/writeSafe&token={TOKEN}'

for remote_path, local_path in files.items():
    with open(local_path, 'r', encoding='utf-8') as f:
        content = f.read()
    r = requests.post(url, json={'path': remote_path, 'content': content}, timeout=30)
    raw = r.content
    if raw.startswith(b'\xef\xbb\xbf'): raw = raw[3:]
    data = json.loads(raw.decode('utf-8'))
    print(remote_path, data.get('status'))

print('Done! URL: https://stroiapp.ru/catalog/view/theme/unishop2/manager/index.html')
