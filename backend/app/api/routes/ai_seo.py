from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import httpx
import json
import ssl

from app.core.config import settings
from app.services.opencart_api import opencart_api

router = APIRouter(prefix="/ai-seo", tags=["ai-seo"])


@router.get("/status")
def ai_seo_status():
    return {"status": "ok", "service": "ai_seo"}

SECRET_TOKEN = "ai-seo-2025-stroiapp-moscow"
DEEPSEEK_API_KEY = getattr(settings, 'deepseek_api_key', '')
OPENCART_API_URL = getattr(settings, 'opencart_api_url', '')
OPENCART_API_TOKEN = getattr(settings, 'opencart_api_token', '')

HTML_PAGE = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI SEO Generator - Moscow Geo</title>
<style>
*{box-sizing:border-box;font-family:system-ui,-apple-system,sans-serif}
body{margin:0;background:#f5f5f5;color:#333}
.container{max-width:1400px;margin:0 auto;padding:20px}
.header{background:#fff;padding:20px;border-radius:8px;margin-bottom:20px;box-shadow:0 1px 3px rgba(0,0,0,.1)}
.header h1{margin:0 0 5px;font-size:24px}
.header p{margin:0;color:#666;font-size:14px}
.toolbar{background:#fff;padding:15px;border-radius:8px;margin-bottom:20px;display:flex;gap:10px;flex-wrap:wrap;align-items:center;box-shadow:0 1px 3px rgba(0,0,0,.1)}
.btn{background:#2563eb;color:#fff;border:none;padding:8px 16px;border-radius:6px;cursor:pointer;font-size:14px}
.btn:hover{background:#1d4ed8}
.btn.secondary{background:#6b7280}
.btn.secondary:hover{background:#4b5563}
.btn.success{background:#16a34a}
.btn.success:hover{background:#15803d}
.btn:disabled{opacity:.5;cursor:not-allowed}
.filter-btn{background:#e5e7eb;color:#374151;border:none;padding:6px 14px;border-radius:6px;cursor:pointer;font-size:13px}
.filter-btn.active{background:#2563eb;color:#fff}
.progress-container{display:none;margin-bottom:15px;background:#fff;padding:15px;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,.1)}
.progress-bar{height:30px;background:#e5e7eb;border-radius:6px;overflow:hidden}
.progress-fill{height:100%;background:#2563eb;color:#fff;display:flex;align-items:center;justify-content:center;font-size:14px;transition:width .3s}
.progress-text{text-align:center;color:#666;font-size:12px;margin-top:5px}
.log-panel{display:none;margin-bottom:15px;background:#fff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,.1);overflow:hidden}
.log-header{padding:8px 15px;background:#f3f4f6;border-bottom:1px solid #e5e7eb;display:flex;justify-content:space-between;align-items:center}
.log-header small{color:#666;font-size:12px}
.log-content{padding:10px 15px;max-height:200px;overflow-y:auto;font-family:monospace;font-size:11px;color:#374151}
.table-wrap{background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.1)}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{padding:10px 12px;text-align:left;border-bottom:1px solid #e5e7eb}
th{background:#f9fafb;font-weight:600;font-size:12px;color:#6b7280}
tr:hover{background:#f9fafb}
.label{display:inline-block;padding:3px 8px;border-radius:4px;font-size:11px;font-weight:500}
.label-green{background:#dcfce7;color:#166534}
.label-orange{background:#ffedd5;color:#9a3412}
.status-cell{white-space:nowrap}
.modal{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.5);display:none;justify-content:center;align-items:center;z-index:1000}
.modal.active{display:flex}
.modal-content{background:#fff;border-radius:8px;max-width:700px;width:90%;max-height:80vh;overflow-y:auto;padding:20px}
.modal-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:15px}
.modal-header h3{margin:0}
.modal-close{background:none;border:none;font-size:20px;cursor:pointer;color:#666}
.preview-body{font-size:13px;line-height:1.6}
.preview-body h4{margin:0 0 10px}
.preview-body hr{border:none;border-top:1px solid #e5e7eb;margin:15px 0}
.preview-body p{margin:5px 0}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>AI SEO Generator</h1>
    <p>Geotargeting: Moscow & Moscow Region | DeepSeek AI</p>
  </div>

  <div class="toolbar">
    <button class="filter-btn active" onclick="setFilter('all')">All</button>
    <button class="filter-btn" onclick="setFilter('no_desc')">No description</button>
    <button class="btn secondary" onclick="selectAll(true)">Select all</button>
    <button class="btn secondary" onclick="selectAll(false)">Deselect</button>
    <div style="flex:1"></div>
    <span style="color:#666;font-size:13px">Batch:</span>
    <button class="btn" onclick="generateBatch(1)" id="btn-1">1</button>
    <button class="btn" onclick="generateBatch(10)" id="btn-10">10</button>
    <button class="btn" onclick="generateBatch(100)" id="btn-100">100</button>
    <button class="btn" onclick="generateBatch(500)" id="btn-500">500</button>
  </div>

  <div class="progress-container" id="progress-container">
    <div class="progress-bar"><div class="progress-fill" id="progress-fill">0%</div></div>
    <div class="progress-text" id="progress-text"></div>
  </div>

  <div class="log-panel" id="log-panel">
    <div class="log-header"><small>Log</small><button class="modal-close" onclick="document.getElementById('log-panel').style.display='none'">&times;</button></div>
    <div class="log-content" id="log-content"></div>
  </div>

  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th style="width:1px"><input type="checkbox" onclick="selectAll(this.checked)"></th>
          <th>ID</th>
          <th>Name</th>
          <th style="width:90px">Description</th>
          <th style="width:70px">Meta</th>
          <th style="width:180px">Action</th>
        </tr>
      </thead>
      <tbody id="products-body"><tr><td colspan="6" style="text-align:center;padding:40px;color:#999">Loading...</td></tr></tbody>
    </table>
  </div>
</div>

<div class="modal" id="preview-modal">
  <div class="modal-content">
    <div class="modal-header"><h3>Preview</h3><button class="modal-close" onclick="closeModal()">&times;</button></div>
    <div class="preview-body" id="preview-body"></div>
  </div>
</div>

<script>
const API_BASE = '/api/ai-seo';
let allProducts = [];
let currentFilter = 'all';

function log(msg) {
  const panel = document.getElementById('log-panel');
  panel.style.display = 'block';
  const content = document.getElementById('log-content');
  const t = new Date().toLocaleTimeString();
  content.innerHTML += '[' + t + '] ' + msg + '<br>';
  content.scrollTop = content.scrollHeight;
}

function setFilter(f) {
  currentFilter = f;
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.toggle('active', b.textContent.toLowerCase().includes(f === 'all' ? 'all' : 'no')));
  renderTable();
}

function selectAll(checked) {
  document.querySelectorAll('.product-cb').forEach(cb => cb.checked = checked);
}

function renderTable() {
  const tbody = document.getElementById('products-body');
  let products = allProducts;
  if (currentFilter === 'no_desc') {
    products = products.filter(p => !p.has_description);
  }
  if (products.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:40px;color:#999">No products</td></tr>';
    return;
  }
  tbody.innerHTML = products.map(p => `<tr id="row-${p.product_id}">
    <td><input type="checkbox" class="product-cb" value="${p.product_id}"></td>
    <td>${p.product_id}</td>
    <td>${escapeHtml(p.name)}</td>
    <td>${p.has_description ? '<span class="label label-green">Yes</span>' : '<span class="label label-orange">No</span>'}</td>
    <td>${p.has_meta ? '<span class="label label-green">Yes</span>' : '<span class="label label-orange">No</span>'}</td>
    <td class="status-cell">
      <button class="btn" style="padding:4px 10px;font-size:12px" onclick="generateOne(${p.product_id})">Generate</button>
      <span id="status-${p.product_id}"></span>
    </td>
  </tr>`).join('');
}

function escapeHtml(s) {
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}

async function loadProducts() {
  try {
    const r = await fetch(API_BASE + '/products');
    const data = await r.json();
    allProducts = data.products || [];
    renderTable();
  } catch (e) {
    document.getElementById('products-body').innerHTML = '<tr><td colspan="6" style="text-align:center;padding:40px;color:#c00">Error: ' + e.message + '</td></tr>';
  }
}

function setStatus(id, html) {
  const el = document.getElementById('status-' + id);
  if (el) el.innerHTML = html;
}

function showPreview(data) {
  const body = document.getElementById('preview-body');
  body.innerHTML = '<h4>' + escapeHtml(data.name) + '</h4>' +
    '<p><strong>Meta Title:</strong> ' + escapeHtml(data.meta_title || '') + '</p>' +
    '<p><strong>Meta Description:</strong> ' + escapeHtml(data.meta_description || '') + '</p>' +
    '<p><strong>Keywords:</strong> ' + escapeHtml(data.meta_keyword || '') + '</p>' +
    '<hr><p>' + escapeHtml(data.description || '') + '</p>';
  document.getElementById('preview-modal').classList.add('active');
}
function closeModal() { document.getElementById('preview-modal').classList.remove('active'); }

async function generateOne(productId) {
  setStatus(productId, '<span style="color:#999">...</span>');
  try {
    const r = await fetch(API_BASE + '/generate', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({product_id: productId})
    });
    const data = await r.json();
    if (data.error) {
      setStatus(productId, '<span style="color:#c00" title="' + escapeHtml(data.error) + '">Error</span>');
      log('ID ' + productId + ' ERROR: ' + data.error);
    } else {
      setStatus(productId, '<span style="color:#16a34a;cursor:pointer" onclick="showPreview(' + JSON.stringify(data).replace(/"/g, '&quot;') + ')">Generated</span>');
      document.getElementById('row-' + productId).style.background = '#f0fdf4';
      log('ID ' + productId + ' OK');
    }
  } catch (e) {
    setStatus(productId, '<span style="color:#c00">Error</span>');
    log('ID ' + productId + ' ERROR: ' + e.message);
  }
}

async function generateBatch(limit) {
  const cbs = document.querySelectorAll('.product-cb:checked');
  if (cbs.length === 0) { alert('Select products'); return; }
  let ids = Array.from(cbs).map(cb => cb.value);
  if (limit > 0) ids = ids.slice(0, limit);

  document.querySelectorAll('.btn').forEach(b => b.disabled = true);
  const prog = document.getElementById('progress-container');
  prog.style.display = 'block';
  const fill = document.getElementById('progress-fill');
  const ptxt = document.getElementById('progress-text');

  let done = 0, ok = 0, fail = 0;
  log('=== Batch: ' + ids.length + ' products ===');

  for (const id of ids) {
    setStatus(id, '<span style="color:#999">...</span>');
    try {
      const r = await fetch(API_BASE + '/generate', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({product_id: id})
      });
      const data = await r.json();
      if (data.error) { setStatus(id, '<span style="color:#c00">Error</span>'); fail++; log('ID ' + id + ' FAIL: ' + data.error); }
      else { setStatus(id, '<span style="color:#16a34a;cursor:pointer" onclick="showPreview(' + JSON.stringify(data).replace(/"/g, '&quot;') + ')">Generated</span>'); document.getElementById('row-' + id).style.background = '#f0fdf4'; ok++; log('ID ' + id + ' OK'); }
    } catch (e) { setStatus(id, '<span style="color:#c00">Error</span>'); fail++; log('ID ' + id + ' FAIL: ' + e.message); }
    done++;
    const pct = Math.round((done / ids.length) * 100);
    fill.style.width = pct + '%'; fill.textContent = pct + '%';
    ptxt.textContent = done + '/' + ids.length + ' (OK:' + ok + ' Fail:' + fail + ')';
    await new Promise(r => setTimeout(r, 300));
  }
  log('=== Done: OK=' + ok + ' Fail=' + fail + ' ===');
  document.querySelectorAll('.btn').forEach(b => b.disabled = false);
}

loadProducts();
</script>
</body>
</html>"""


class GeneratePayload(BaseModel):
    product_id: int


@router.get("", response_class=HTMLResponse)
async def ai_seo_page():
    return HTMLResponse(content=HTML_PAGE)


@router.get("/products")
async def get_products():
    try:
        data = await opencart_api.get_action("product/list", {"limit": 1000, "page": 1})
        products = []
        for p in data.get("products", []):
            desc = p.get("description", "")
            meta = p.get("meta_title", "")
            has_desc = bool(desc) and len(desc) > 50
            has_meta = bool(meta) and len(meta) > 5
            products.append({
                "product_id": p.get("product_id", 0),
                "name": p.get("name", ""),
                "has_description": has_desc,
                "has_meta": has_meta,
            })
        return {"products": products}
    except Exception as exc:
        return {"products": [], "error": str(exc)}


@router.post("/generate")
async def generate(payload: GeneratePayload):
    try:
        # Get product details
        product = await opencart_api.get_action("product/get", {"product_id": payload.product_id})
        product_name = product.get("name", "")
        category_name = product.get("category_name", "Stroitelnye materialy")

        # DeepSeek prompt
        prompt = (
            f"Napishi unikalnoe SEO-opisanie tovara dlya internet-magazina stroitelnyh materialov v Moskve i Moskovskoy oblasti.\n\n"
            f"Tovar: {product_name}\n"
            f"Kategoriya: {category_name}\n\n"
            "Treboniya:\n"
            "1. Opisanie: 400-600 znakov, unikalnoe, informativnoe\n"
            "2. Vklyuchi geotargeting: Moskva, Moskovskaya oblast, dostavka, opt\n"
            "3. Preimushchestva dlya stroiteley i remontnikov\n"
            "4. Professionalnyy ton, dostupnyy yazyik\n"
            "5. Prizyv k deystviyu v kontse\n"
            "6. Meta title: 50-60 znakov\n"
            "7. Meta description: 150-160 znakov\n"
            "8. Meta keywords: 5-7 slov cherez zapyatuyu\n\n"
            "Verny rezultat v formate JSON s polyami: description, meta_title, meta_description, meta_keyword"
        )

        ds_payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "Tyi - SEO-kopirayter dlya stroitelnyh materialov v Moskve. Piši na russkom."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 1500,
            "response_format": {"type": "json_object"}
        }

        import urllib.request as _urllib_req
        _ds_ctx = ssl.create_default_context()
        _ds_ctx.check_hostname = False
        _ds_ctx.verify_mode = ssl.CERT_NONE
        _ds_data = json.dumps(ds_payload).encode("utf-8")
        _ds_req = _urllib_req.Request(
            "https://api.deepseek.com/v1/chat/completions",
            data=_ds_data,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {DEEPSEEK_API_KEY}"},
            method="POST",
        )
        with _urllib_req.urlopen(_ds_req, timeout=60, context=_ds_ctx) as _ds_resp:
            result = json.loads(_ds_resp.read().decode("utf-8-sig"))

        content = json.loads(result["choices"][0]["message"]["content"])
        description = content.get("description", "")
        meta_title = content.get("meta_title", product_name)
        meta_description = content.get("meta_description", "")
        meta_keyword = content.get("meta_keyword", "")

        # Save via OpenCart API
        await opencart_api.post_action("seo/updateMeta", {
            "product_id": payload.product_id,
            "language_id": 1,
            "meta_title": meta_title,
            "meta_description": meta_description,
            "meta_keyword": meta_keyword,
        })

        # Also update description via product update
        await opencart_api.post_action("product/update", {
            "product_id": payload.product_id,
            "description": description,
        })

        return {
            "success": True,
            "product_id": payload.product_id,
            "name": product_name,
            "description": description,
            "meta_title": meta_title,
            "meta_description": meta_description,
            "meta_keyword": meta_keyword,
        }
    except Exception as exc:
        return {"error": str(exc)}
