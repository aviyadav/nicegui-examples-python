$URL = "http://localhost:8080/sensor"
$COUNT = 100
$INTERVAL = 0.5  # seconds between each request

Write-Host "Sending $COUNT random temperatures to $URL ..."

for ($i = 1; $i -le $COUNT; $i++) {
    # Generate a random temperature between 15.0 and 45.0 with 1 decimal place
    $temp = [math]::Round(15 + (Get-Random -Minimum 0.0 -Maximum 30.0), 1)
    Write-Host "[$i/$COUNT] Sending temperature: ${temp}°C"
    curl.exe -s -X POST "${URL}?temperature=${temp}" | Out-Null
    Start-Sleep -Seconds $INTERVAL
}

Write-Host "Done."
