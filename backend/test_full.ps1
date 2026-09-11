$base = 'http://127.0.0.1:8000/api'
$results = @()

function Test-Endpoint($method, $path, $name, $body) {
    try {
        if ($method -eq 'GET') {
            $r = Invoke-RestMethod -Uri ($base + $path) -Method GET -ErrorAction Stop
        } elseif ($method -eq 'POST') {
            if ($body) {
                $json = $body | ConvertTo-Json -Depth 5
                $r = Invoke-RestMethod -Uri ($base + $path) -Method POST -Body $json -ContentType 'application/json' -ErrorAction Stop
            } else {
                $r = Invoke-RestMethod -Uri ($base + $path) -Method POST -ContentType 'application/json' -ErrorAction Stop
            }
        } elseif ($method -eq 'DELETE') {
            $r = Invoke-RestMethod -Uri ($base + $path) -Method DELETE -ErrorAction Stop
        }
        return 'OK'
    } catch {
        $code = $_.Exception.Response.StatusCode.value__
        return "ERR $code"
    }
}

# === DASHBOARD ===
$results += ,@('Dashboard', (Test-Endpoint 'GET' '/dashboard/compare' 'Dashboard' $null))
$results += ,@('Campaigns', (Test-Endpoint 'GET' '/dashboard/campaigns' 'Campaigns' $null))
$results += ,@('CalcBudget', (Test-Endpoint 'POST' '/dashboard/calculate' 'CalcBudget' @{budget=50000}))
$results += ,@('Profitable', (Test-Endpoint 'GET' '/dashboard/profitableProducts?min_roi=100&limit=5' 'Profitable' $null))

# === PRODUCTS ===
$results += ,@('Prod-List', (Test-Endpoint 'GET' '/product/list?limit=5' 'Prod-List' $null))
$results += ,@('Prod-Search', (Test-Endpoint 'GET' '/product/list?search=cement&limit=3' 'Prod-Search' $null))
$results += ,@('Prod-Filter', (Test-Endpoint 'GET' '/product/list?min_price=100&max_price=5000&sort_by=roi&limit=3' 'Prod-Filter' $null))
$results += ,@('Prod-Get', (Test-Endpoint 'GET' '/product/get/00001' 'Prod-Get' $null))

# === SEO ===
$results += ,@('SEO-Bulk', (Test-Endpoint 'GET' '/seo/bulkGenerate?limit=2' 'SEO-Bulk' $null))
$results += ,@('SEO-GenDesc', (Test-Endpoint 'POST' '/seo/generateDescription' 'SEO-GenDesc' @{sku='00001'; name='Test'; url='https://stroiapp.ru'}))
$results += ,@('SEO-FAQ', (Test-Endpoint 'POST' '/seo/generateFAQ' 'SEO-FAQ' @{sku='00001'; name='Test'; url='https://stroiapp.ru'}))

# === COMPETITORS ===
$results += ,@('Comp-List', (Test-Endpoint 'GET' '/competitors/list' 'Comp-List' $null))

# === COMPETITORS-BIDS ===
$results += ,@('Bids-Status', (Test-Endpoint 'GET' '/competitors-bids/status' 'Bids-Status' $null))
$results += ,@('Bids-List', (Test-Endpoint 'GET' '/competitors-bids/list' 'Bids-List' $null))
$results += ,@('Bids-Compare', (Test-Endpoint 'GET' '/competitors-bids/compare' 'Bids-Compare' $null))
$results += ,@('Bids-Top', (Test-Endpoint 'GET' '/competitors-bids/top?limit=5' 'Bids-Top' $null))
$results += ,@('Bids-Ads', (Test-Endpoint 'GET' '/competitors-bids/ads?limit=5' 'Bids-Ads' $null))
$results += ,@('Bids-AdsStats', (Test-Endpoint 'GET' '/competitors-bids/ads-stats' 'Bids-AdsStats' $null))
$results += ,@('Bids-Recs', (Test-Endpoint 'GET' '/competitors-bids/recommendations?top_n=5' 'Bids-Recs' $null))

# === OPENCART ===
$results += ,@('OC-Health', (Test-Endpoint 'GET' '/opencart/health' 'OC-Health' $null))
$results += ,@('OC-SyncPrices', (Test-Endpoint 'GET' '/opencart/syncPrices' 'OC-SyncPrices' $null))
$results += ,@('OC-Orders', (Test-Endpoint 'GET' '/opencart/orders/list?limit=10&page=1' 'OC-Orders' $null))
$results += ,@('OC-Cats', (Test-Endpoint 'GET' '/opencart/categories/tree' 'OC-Cats' $null))
$results += ,@('OC-CatsList', (Test-Endpoint 'GET' '/opencart/categories/list' 'OC-CatsList' $null))
$results += ,@('OC-Customers', (Test-Endpoint 'GET' '/opencart/customers/list?limit=10&page=1' 'OC-Customers' $null))
$results += ,@('OC-CustGroups', (Test-Endpoint 'GET' '/opencart/customer/groups' 'OC-CustGroups' $null))
$results += ,@('OC-Products', (Test-Endpoint 'GET' '/opencart/products/list?limit=10&page=1' 'OC-Products' $null))
$results += ,@('OC-Banners', (Test-Endpoint 'GET' '/opencart/banners/list' 'OC-Banners' $null))
$results += ,@('OC-Settings', (Test-Endpoint 'GET' '/opencart/settings/list' 'OC-Settings' $null))
$results += ,@('OC-SiteHealth', (Test-Endpoint 'GET' '/opencart/site/health' 'OC-SiteHealth' $null))
$results += ,@('OC-SiteErrLog', (Test-Endpoint 'GET' '/opencart/site/errorLog' 'OC-SiteErrLog' $null))
$results += ,@('OC-SiteBackups', (Test-Endpoint 'GET' '/opencart/site/backups' 'OC-SiteBackups' $null))
$results += ,@('OC-SiteBrokenImg', (Test-Endpoint 'GET' '/opencart/site/findBrokenImages' 'OC-SiteBrokenImg' $null))
$results += ,@('OC-SEOStats', (Test-Endpoint 'GET' '/opencart/seo/productStats' 'OC-SEOStats' $null))
$results += ,@('OC-Files', (Test-Endpoint 'GET' '/opencart/files/list?path=catalog/' 'OC-Files' $null))
$results += ,@('OC-Special', (Test-Endpoint 'GET' '/opencart/special-products?limit=4' 'OC-Special' $null))
$results += ,@('OC-SpecialAll', (Test-Endpoint 'GET' '/opencart/special-prices/all?limit=10' 'OC-SpecialAll' $null))

# === BUDGET-ROI ===
$results += ,@('Budget-Status', (Test-Endpoint 'GET' '/budget-roi/status' 'Budget-Status' $null))
$results += ,@('Budget-Forecast', (Test-Endpoint 'GET' '/budget-roi/forecast?days=30' 'Budget-Forecast' $null))
$results += ,@('Budget-Calc', (Test-Endpoint 'POST' '/budget-roi/calculate' 'Budget-Calc' @{budget=50000}))

# === PROMOTIONS ===
$results += ,@('Promo-List', (Test-Endpoint 'GET' '/promotions/list' 'Promo-List' $null))

# === REVIEWS ===
$results += ,@('Reviews-Status', (Test-Endpoint 'GET' '/reviews/status' 'Reviews-Status' $null))

# === AUTOSMETA ===
$results += ,@('Autosmeta-Status', (Test-Endpoint 'GET' '/autosmeta/status' 'Autosmeta-Status' $null))

# === CONTENT-FACTORY ===
$results += ,@('Content-Status', (Test-Endpoint 'GET' '/content-factory/status' 'Content-Status' $null))
$results += ,@('Content-Queue', (Test-Endpoint 'GET' '/content-factory/queue' 'Content-Queue' $null))

# === CLIENTS-OBJECTS ===
$results += ,@('Clients-Status', (Test-Endpoint 'GET' '/clients-objects/status' 'Clients-Status' $null))
$results += ,@('Clients-List', (Test-Endpoint 'GET' '/clients-objects/clients' 'Clients-List' $null))
$results += ,@('Objects-List', (Test-Endpoint 'GET' '/clients-objects/objects' 'Objects-List' $null))

# === SYNC ===
$results += ,@('Sync-Status', (Test-Endpoint 'GET' '/sync/status' 'Sync-Status' $null))

# === SITE BUILDER ===
$results += ,@('SB-Status', (Test-Endpoint 'GET' '/site-builder/status' 'SB-Status' $null))
$results += ,@('SB-Blocks', (Test-Endpoint 'GET' '/site-builder/blocks?page=home' 'SB-Blocks' $null))
$results += ,@('SB-BlockTypes', (Test-Endpoint 'GET' '/site-builder/block-types' 'SB-BlockTypes' $null))

# === AI-SEO ===
$results += ,@('AISEO-Products', (Test-Endpoint 'GET' '/ai-seo/products' 'AISEO-Products' $null))

# === GEO ===
$results += ,@('Geo-Cities', (Test-Endpoint 'GET' '/geo/cities' 'Geo-Cities' $null))
$results += ,@('Geo-Regions', (Test-Endpoint 'GET' '/geo/regions' 'Geo-Regions' $null))
$results += ,@('Geo-Detect', (Test-Endpoint 'GET' '/geo/detect' 'Geo-Detect' $null))

# === TENDERS ===
$results += ,@('Tenders-Status', (Test-Endpoint 'GET' '/tenders/status' 'Tenders-Status' $null))
$results += ,@('Tenders-Search', (Test-Endpoint 'POST' '/tenders/search' 'Tenders-Search' @{region='Moscow'}))

# === TELEGRAM ===
$results += ,@('Telegram-Test', (Test-Endpoint 'POST' '/telegram/test' 'Telegram-Test' $null))

# === SPECULATION ===
$results += ,@('Spec-Rules', (Test-Endpoint 'GET' '/speculation/rules' 'Spec-Rules' $null))

# === AI-DEEPSEEK ===
$results += ,@('AI-DS-Status', (Test-Endpoint 'GET' '/ai-deepseek/status' 'AI-DS-Status' $null))

# === LEAD ===
$results += ,@('Lead-Status', (Test-Endpoint 'GET' '/lead/status' 'Lead-Status' $null))

# === HEALTH ===
$results += ,@('Health', (Test-Endpoint 'GET' '/health' 'Health' $null))

# Print results
$ok = 0
$err = 0
foreach ($r in $results) {
    $name = $r[0]
    $status = $r[1]
    Write-Output ('{0,-22} {1}' -f $name, $status)
    if ($status -eq 'OK') { $ok++ } else { $err++ }
}
Write-Output ''
Write-Output "Total: $($results.Count)  OK: $ok  ERR: $err"
