$base = 'http://127.0.0.1:8000/api'
$baseRoot = 'http://127.0.0.1:8000'
$results = @()

function Test-Endpoint($method, $path, $name, $body, $root) {
    $url = if ($root) { $baseRoot + $path } else { $base + $path }
    try {
        if ($method -eq 'GET') {
            $r = Invoke-RestMethod -Uri $url -Method GET -ErrorAction Stop
        } elseif ($method -eq 'POST') {
            if ($body) {
                $json = $body | ConvertTo-Json -Depth 5
                $r = Invoke-RestMethod -Uri $url -Method POST -Body $json -ContentType 'application/json' -ErrorAction Stop
            } else {
                $r = Invoke-RestMethod -Uri $url -Method POST -ContentType 'application/json' -ErrorAction Stop
            }
        }
        return 'OK'
    } catch {
        $code = $_.Exception.Response.StatusCode.value__
        return "ERR $code"
    }
}

# Fix previously wrong paths
$results += ,@('AI-DS-Status', (Test-Endpoint 'GET' '/ai/deepseek/status' 'AI-DS-Status' $null $false))
$results += ,@('Lead-INN', (Test-Endpoint 'GET' '/lead/validateInn?inn=7707083893' 'Lead-INN' $null $false))
$results += ,@('Health', (Test-Endpoint 'GET' '/health' 'Health' $null $true))

# Re-test previously failing
$results += ,@('Budget-Calc', (Test-Endpoint 'POST' '/budget-roi/calculate' 'Budget-Calc' @{budget=50000} $false))
$results += ,@('Tenders-Search', (Test-Endpoint 'POST' '/tenders/search' 'Tenders-Search' @{region='Moscow'} $false))

# Get a real SKU for Prod-Get test
$prods = Invoke-RestMethod -Uri ($base + '/product/list?limit=1') -Method GET
$sku = $prods[0].sku
$results += ,@("Prod-Get($sku)", (Test-Endpoint 'GET' "/product/get/$sku" "Prod-Get" $null $false))

$ok = 0; $err = 0
foreach ($r in $results) {
    Write-Output ('{0,-22} {1}' -f $r[0], $r[1])
    if ($r[1] -eq 'OK') { $ok++ } else { $err++ }
}
Write-Output ''
Write-Output "Total: $($results.Count)  OK: $ok  ERR: $err"
