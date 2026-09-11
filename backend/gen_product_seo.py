import urllib.request, ssl, json, socket, re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

ip = socket.gethostbyname("stroiapp.ru")
h = {"Content-Type": "application/json", "X-AI-Token": "change_this_ai_manager_token", "Host": "stroiapp.ru"}

def post(action, payload, timeout=60):
    d = json.dumps(payload).encode()
    req = urllib.request.Request(f"https://{ip}/index.php?route=api/ai_manager&action={action}", data=d, headers=h, method="POST")
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        return json.loads(r.read().decode("utf-8-sig"))

# Russian transliteration map
TRANS = {
    'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'e','ж':'zh','з':'z',
    'и':'i','й':'y','к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','р':'r',
    'с':'s','т':'t','у':'u','ф':'f','х':'h','ц':'ts','ч':'ch','ш':'sh','щ':'sch',
    'ъ':'','ы':'y','ь':'','э':'e','ю':'yu','я':'ya',
    ' ':"-","_":"-","(":"",")":"",",":"",".":"","/":"-","\\":"-",
    '"':"","'":"","!":"","?":"",":":"",";":"","+":"-","№":"",
}

def slugify(name):
    s = name.lower().strip()
    result = []
    for ch in s:
        if ch in TRANS:
            result.append(TRANS[ch])
        elif ch.isalnum() and ord(ch) < 128:
            result.append(ch)
    slug = ''.join(result)
    slug = re.sub(r'-{2,}', '-', slug)
    slug = slug.strip('-')
    if len(slug) > 80:
        slug = slug[:80].rsplit('-', 1)[0]
    return slug

# Get all products
r = post("db/select", {"sql": "SELECT p.product_id, pd.name FROM oc_openproduct p JOIN oc_openproduct_description pd ON p.product_id = pd.product_id WHERE pd.language_id = 1"})
products = r.get('rows', [])
print(f"Total products: {len(products)}")

# Generate and insert SEO URLs
inserted = 0
skipped = 0
seen_slugs = {}

for p in products:
    pid = p['product_id']
    slug = slugify(p['name'])
    
    if not slug:
        slug = f"product-{pid}"
    
    # Ensure unique slug
    if slug in seen_slugs:
        slug = f"{slug}-{pid}"
    seen_slugs[slug] = True
    
    # Check if already exists
    check = post("db/select", {"sql": f"SELECT * FROM oc_openseo_url WHERE `query` = 'product_id={pid}' AND store_id = 0 AND language_id = 1"})
    if check.get('rows'):
        skipped += 1
        continue
    
    # Insert
    sql = f"INSERT INTO oc_openseo_url (store_id, language_id, `query`, keyword) VALUES (0, 1, 'product_id={pid}', '{slug}')"
    try:
        post("db/executeSql", {"sql": sql})
        inserted += 1
        if inserted % 50 == 0:
            print(f"  Inserted {inserted} SEO URLs...")
    except Exception as e:
        print(f"  Error for product {pid}: {e}")

print(f"\nInserted: {inserted}, Skipped: {skipped}")

# Verify
r2 = post("db/select", {"sql": "SELECT COUNT(*) as cnt FROM oc_openseo_url WHERE `query` LIKE 'product_id=%'"})
print(f"Total product SEO URLs: {r2['rows'][0]['cnt']}")

r3 = post("db/select", {"sql": "SELECT * FROM oc_openseo_url WHERE `query` LIKE 'product_id=%' LIMIT 10"})
print(f"\nSample:")
for row in r3.get('rows', []):
    print(f"  {row['query']} → {row['keyword']}")

print("\n=== DONE ===")
