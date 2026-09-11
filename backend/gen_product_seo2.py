import urllib.request, ssl, json, socket, re, time

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

ip = socket.gethostbyname("stroiapp.ru")
h = {"Content-Type": "application/json", "X-AI-Token": "change_this_ai_manager_token", "Host": "stroiapp.ru"}

def post(action, payload, timeout=30, retries=3):
    for attempt in range(retries):
        try:
            d = json.dumps(payload).encode()
            req = urllib.request.Request(f"https://{ip}/index.php?route=api/ai_manager&action={action}", data=d, headers=h, method="POST")
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
                return json.loads(r.read().decode("utf-8-sig"))
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2)
            else:
                raise

# Check current count
r1 = post("db/select", {"sql": "SELECT COUNT(*) as cnt FROM oc_openseo_url WHERE `query` LIKE 'product_id=%'"})
current = int(r1['rows'][0]['cnt'])
print(f"Current product SEO URLs: {current}")

# Get all products that don't have SEO URLs yet
r2 = post("db/select", {"sql": "SELECT p.product_id, pd.name FROM oc_openproduct p JOIN oc_openproduct_description pd ON p.product_id = pd.product_id WHERE pd.language_id = 1 AND p.product_id NOT IN (SELECT CAST(SUBSTRING(`query`, 12) AS UNSIGNED) FROM oc_openseo_url WHERE `query` LIKE 'product_id=%')"})
products = r2.get('rows', [])
print(f"Remaining products without SEO URL: {len(products)}")

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
    return slug if slug else "product"

# Get existing slugs to avoid duplicates
r3 = post("db/select", {"sql": "SELECT keyword FROM oc_openseo_url WHERE `query` LIKE 'product_id=%'"})
existing_slugs = set(row['keyword'] for row in r3.get('rows', []))

inserted = 0
for p in products:
    pid = p['product_id']
    slug = slugify(p['name'])
    
    if slug in existing_slugs:
        slug = f"{slug}-{pid}"
    existing_slugs.add(slug)
    
    sql = f"INSERT INTO oc_openseo_url (store_id, language_id, `query`, keyword) VALUES (0, 1, 'product_id={pid}', '{slug}')"
    try:
        post("db/executeSql", {"sql": sql}, retries=2)
        inserted += 1
        if inserted % 50 == 0:
            print(f"  Inserted {inserted}...")
    except Exception as e:
        print(f"  Error product {pid}: {e}")
        time.sleep(1)

print(f"\nInserted: {inserted}")

# Final count
r4 = post("db/select", {"sql": "SELECT COUNT(*) as cnt FROM oc_openseo_url WHERE `query` LIKE 'product_id=%'"})
print(f"Total product SEO URLs: {r4['rows'][0]['cnt']}")

# Sample
r5 = post("db/select", {"sql": "SELECT * FROM oc_openseo_url WHERE `query` LIKE 'product_id=%' LIMIT 10"})
print(f"\nSample:")
for row in r5.get('rows', []):
    print(f"  {row['query']} → {row['keyword']}")

print("\n=== DONE ===")
