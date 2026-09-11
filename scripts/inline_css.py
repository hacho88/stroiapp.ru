"""Inline CSS into home.twig and upload."""
import requests, json

with open('D:/Projects/ai.stroiapp.ru/stroiapp.ru/public_html/catalog/view/theme/unishop2/stylesheet/ai_home.css', 'rb') as f:
    css = f.read().decode('utf-8')

with open('D:/Projects/ai.stroiapp.ru/stroiapp.ru/public_html/catalog/view/theme/unishop2/template/common/home.twig', 'rb') as f:
    twig = f.read().decode('utf-8')

twig = twig.replace(
    '<link rel="stylesheet" href="catalog/view/theme/unishop2/stylesheet/ai_home.css">',
    f'<style>\n{css}\n</style>'
)

OPENCART_URL = 'https://stroiapp.ru'
TOKEN = 'change_this_ai_manager_token'

url = f'{OPENCART_URL}/index.php?route=api/ai_manager&action=file/writeSafe&token={TOKEN}'
r = requests.post(url, json={'path': 'catalog/view/theme/unishop2/template/common/home.twig', 'content': twig}, timeout=30)
raw = r.content
if raw.startswith(b'\xef\xbb\xbf'): raw = raw[3:]
data = json.loads(raw.decode('utf-8'))
print('twig:', data.get('status'))

cache_url = f'{OPENCART_URL}/index.php?route=api/ai_manager&action=site/clearCache&token={TOKEN}'
r2 = requests.post(cache_url, timeout=30)
raw2 = r2.content
if raw2.startswith(b'\xef\xbb\xbf'): raw2 = raw2[3:]
data2 = json.loads(raw2.decode('utf-8'))
print('cache:', data2.get('deleted', 0))
print('twig size:', len(twig))
