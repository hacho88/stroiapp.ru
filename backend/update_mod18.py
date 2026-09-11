import urllib.request, ssl, json

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
BASE = "https://stroiapp.ru"
h = {"Content-Type": "application/json", "X-AI-Token": "change_this_ai_manager_token"}

def post(action, payload, timeout=30):
    d = json.dumps(payload).encode()
    req = urllib.request.Request(f"{BASE}/index.php?route=api/ai_manager&action={action}", data=d, headers=h, method="POST")
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        return json.loads(r.read().decode("utf-8-sig"))

# Update modification #18 XML to handle & in query
new_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<modification>
<name>Geo Page SEO Routing</name>
<code>geo_seo_routing</code>
<version>2.0</version>
<author>AI Manager</author>
    <file path="catalog/controller/startup/seo_url.php">
        <operation error="skip">
            <search><![CDATA[array_pop($parts);]]></search>
            <add position="after"><![CDATA[
                // Geo page routing: /geo/product-keyword/city-id
                if (count($parts) >= 3 && $parts[0] == 'geo') {
                    $pquery = $this->db->query("SELECT * FROM " . DB_PREFIX . "seo_url WHERE keyword = '" . $this->db->escape($parts[1]) . "' AND store_id = '" . (int)$this->config->get('config_store_id') . "'");
                    if ($pquery->num_rows) {
                        $purl = explode('=', $pquery->row['query']);
                        if ($purl[0] == 'product_id') {
                            $this->request->get['product_id'] = $purl[1];
                            $this->request->get['city_id'] = $parts[2];
                            $this->request->get['route'] = 'product/geo';
                            return;
                        }
                    }
                }
]]></add>
        </operation>
        <operation error="skip">
            <search><![CDATA[if ($query->num_rows) {
					$url = explode('=', $query->row['query']);]]></search>
            <add position="replace"><![CDATA[if ($query->num_rows) {
					// Handle queries with & (e.g. product/product&geo_id=88012)
					if (strpos($query->row['query'], '&') !== false) {
						$qparts = explode('&', $query->row['query']);
						$this->request->get['route'] = $qparts[0];
						for ($gi = 1; $gi < count($qparts); $gi++) {
							$gpair = explode('=', $qparts[$gi], 2);
							if (count($gpair) == 2) {
								$this->request->get[$gpair[0]] = $gpair[1];
							}
						}
					} else {
					$url = explode('=', $query->row['query']);]]></add>
        </operation>
        <operation error="skip">
            <search><![CDATA[if ($query->row['query'] && $url[0] != 'information_id' && $url[0] != 'manufacturer_id' && $url[0] != 'category_id' && $url[0] != 'product_id') {
						$this->request->get['route'] = $query->row['query'];
					}
				} else {]]></search>
            <add position="replace"><![CDATA[if ($query->row['query'] && $url[0] != 'information_id' && $url[0] != 'manufacturer_id' && $url[0] != 'category_id' && $url[0] != 'product_id') {
						$this->request->get['route'] = $query->row['query'];
					}
					} // end else (no & in query)
				} else {]]></add>
        </operation>
    </file>
    <file path="catalog/controller/product/product.php">
        <operation error="skip">
            <search><![CDATA[if (isset($this->request->get['product_id'])) {
            $product_id = (int)$this->request->get['product_id'];
        } else {
            $product_id = 0;
        }]]></search>
            <add position="replace"><![CDATA[if (isset($this->request->get['product_id'])) {
            $product_id = (int)$this->request->get['product_id'];
        } else {
            $product_id = 0;
        }

        // Geo page: if geo_id is set, look up product_id and geo data
        $geo_data = null;
        if (isset($this->request->get['geo_id'])) {
            $geo_id = (int)$this->request->get['geo_id'];
            $geo_query = $this->db->query("SELECT * FROM `oc_product_geo` WHERE product_geo_id = '" . (int)$geo_id . "' LIMIT 1");
            if ($geo_query->num_rows) {
                $geo_data = $geo_query->row;
                if ($product_id == 0) {
                    $product_id = (int)$geo_data['product_id'];
                    $this->request->get['product_id'] = $product_id;
                }
            }
        }]]></add>
        </operation>
        <operation error="skip">
            <search><![CDATA[$this->document->setTitle($product_info['meta_title']);
            $this->document->setDescription($product_info['meta_description']);
            $this->document->setKeywords($product_info['meta_keyword']);]]></search>
            <add position="replace"><![CDATA[$this->document->setTitle($product_info['meta_title']);
            $this->document->setDescription($product_info['meta_description']);
            $this->document->setKeywords($product_info['meta_keyword']);

            // Geo page overrides
            if ($geo_data) {
                if (!empty($geo_data['seo_title'])) {
                    $this->document->setTitle($geo_data['seo_title']);
                }
                if (!empty($geo_data['seo_description'])) {
                    $this->document->setDescription($geo_data['seo_description']);
                }
            }]]></add>
        </operation>
        <operation error="skip">
            <search><![CDATA[$data['description'] = html_entity_decode($product_info['description'], ENT_QUOTES, 'UTF-8');]]></search>
            <add position="after"><![CDATA[
            // Geo page: override description
            if ($geo_data && !empty($geo_data['description'])) {
                $data['description'] = html_entity_decode($geo_data['description'], ENT_QUOTES, 'UTF-8');
            }]]></add>
        </operation>
    </file>
</modification>'''

# Escape XML for SQL
escaped_xml = new_xml.replace("\\", "\\\\").replace("'", "\\'")

sql = f"UPDATE `oc_openmodification` SET `xml` = '{escaped_xml}', `version` = '2.0' WHERE `modification_id` = 18"

print("=== Update modification #18 ===")
r = post("db/executeSql", {"sql": sql})
print(f"  Result: {r}")

# Verify
r2 = post("db/executeSql", {"sql": "SELECT modification_id, name, version, LEFT(xml, 200) as xml_start FROM `oc_openmodification` WHERE `modification_id` = 18"})
print(f"\n  Verify: {r2.get('rows', [])}")

print("\nDONE")
