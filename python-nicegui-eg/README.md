# python-nicegui-eg

A collection of [NiceGUI](https://nicegui.io/) examples demonstrating common UI patterns in Python.

## Requirements

- Python >= 3.14
- [uv](https://docs.astral.sh/uv/) package manager

## Dependencies

| Package    | Version   |
|------------|-----------|
| nicegui    | >=3.8.0   |
| fastapi    | >=0.135.1 |
| uvicorn    | >=0.41.0  |

## Running Examples

Use `uv run` to run any example directly:

```sh
uv run <filename>.py
```

---

## Examples

### `main.py` — Basic Button & Notification

A simple example showing a label, a blocking report generator, and a notification on completion.

```sh
uv run main.py
```

- Renders a label and a **Run Report** button.
- Clicking the button calls a synchronous function that sleeps for 2 seconds and then shows a notification.

---

### `handle-long-running-tasks.py` — Async Progress Bar

Demonstrates how to handle long-running tasks without blocking the UI using `async`/`await`.

```sh
uv run handle-long-running-tasks.py
```

- Renders a linear progress bar and a **Start Sync** button.
- Clicking the button runs an `async` function that increments the progress bar by `0.1` every second over 10 steps (0 → 100%).
- Shows a **"Data sync complete"** notification when done.

> **Key pattern:** Pass the `async` coroutine directly as `on_click=sync_data` instead of wrapping it in `asyncio.create_task()`. NiceGUI's event system natively awaits async handlers while preserving the UI slot context, avoiding a `RuntimeError`.

---

### `map-loc.py` — Sub-pages & Interactive Map

Demonstrates NiceGUI sub-page routing and the Leaflet map component.

```sh
uv run map-loc.py
```

- The `/` route renders a **table** of cities with their coordinates.
- Clicking a row navigates to `/map/{lat}/{lon}`, which renders an interactive **Leaflet map** centred on that city.
- A **Back to table** link returns to the table.

| City      | Latitude | Longitude |
|-----------|----------|-----------|
| New York  | 40.7119  | -74.0027  |
| London    | 51.5074  | -0.1278   |
| Tokyo     | 35.6863  | 139.7722  |
| Patna     | 25.6139  | 85.1312   |
| Bengaluru | 12.9716  | 77.5946   |

> **Key pattern:** Use `ui.sub_pages({...})` for client-side routing and `ui.navigate.to(path)` to navigate programmatically from event handlers.

---

### `event-trigger-chart.py` — Real-time Scrolling Chart via Webhook

Demonstrates how to drive a live-updating ECharts line chart from an external HTTP event source using NiceGUI's `Event` system.

```sh
uv run event-trigger-chart.py
```

- Exposes a `POST /sensor?temperature=<value>` FastAPI webhook endpoint.
- Each POST emits a `sensor` event carrying the temperature value.
- The chart subscribes to the event and appends `[timestamp_ms, temperature]` data points, keeping the last **20** readings (scrolling window).
- The chart updates live in the browser via `chart.update()` after each new data point.
- Subscriptions are automatically cleaned up when the page is closed or reloaded to prevent stale handlers.

> **Key patterns:**
> - Use `Event[T]` for type-safe cross-layer communication between HTTP endpoints and the UI.
> - ECharts `"type": "time"` axis expects timestamps in **milliseconds** — use `time.time() * 1000`.
> - Always call `chart.update()` after mutating `chart.options` in Python.
> - Store the return value of `sensor.subscribe(...)` and call `.unsubscribe()` on the chart's `"delete"` event to avoid subscription leaks.

---

### `send-temperatures.sh` — Simulate Sensor Data

A shell script that simulates a sensor by sending 100 random temperature readings to the webhook endpoint.

```sh
./send-temperatures.sh
```

- Sends **100 POST requests** to `http://localhost:8080/sensor?temperature=<value>`.
- Each temperature is a random float between **15.0°C and 45.0°C** with 1 decimal place.
- Waits **0.5 seconds** between requests so the chart scrolls smoothly.
- Prints live progress for each request (`[i/100] Sending temperature: X°C`).

> **Usage:** Start `event-trigger-chart.py` first, open `http://localhost:8080` in a browser, then run the script in a separate terminal to watch the chart scroll in real time. Adjust the `INTERVAL` variable at the top of the script to control the speed.