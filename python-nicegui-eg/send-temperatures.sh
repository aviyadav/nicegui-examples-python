#!/bin/sh

URL="http://localhost:8080/sensor"
COUNT=100
INTERVAL=0.5  # seconds between each request

echo "Sending $COUNT random temperatures to $URL ..."

for i in $(seq 1 $COUNT); do
    # Generate a random temperature between 15.0 and 45.0 with 1 decimal place
    temp=$(awk 'BEGIN { srand(); printf "%.1f", 15 + rand() * 30 }')
    echo "[$i/$COUNT] Sending temperature: ${temp}°C"
    curl -s -X POST "${URL}?temperature=${temp}" > /dev/null
    sleep $INTERVAL
done

echo "Done."
