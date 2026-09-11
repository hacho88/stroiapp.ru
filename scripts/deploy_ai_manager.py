import requests, json

with open('D:/Projects/ai.stroiapp.ru/stroiapp.ru/public_html/catalog/controller/api/ai_manager.php', 'r', encoding='utf-8') as f:
    php = f.read()

OPENCART_URL = 'https://stroiapp.ru'
TOKEN = 'change_this_ai_manager_token'

url = f'{OPENCART_URL}/index.php?route=api/ai_manager&action=file/writeSafe&token={TOKEN}'
r = requests.post(url, json={'path': 'catalog/controller/api/ai_manager.php', 'content': php}, timeout=30)
raw = r.content
if raw.startswith(b'\xef\xbb\xbf'): raw = raw[3:]
data = json.loads(raw.decode('utf-8'))
print('ai_manager.php:', data.get('status'))

cache_url = f'{OPENCART_URL}/index.php?route=api/ai_manager&action=site/clearCache&token={TOKEN}'
r2 = requests.post(cache_url, timeout=30)
raw2 = r2.content
if raw2.startswith(b'\xef\xbb\xbf'): raw2 = raw2[3:]
data2 = json.loads(raw2.decode('utf-8'))
print('cache:', data2.get('deleted', 0))
