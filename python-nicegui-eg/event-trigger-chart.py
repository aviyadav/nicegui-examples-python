import time

from nicegui import Event, app, ui

sensor = Event[float]()


@app.post("/sensor")
def sensor_webhook(temperature: float):
    sensor.emit(temperature)


def root():
    chart = ui.echart(
        {
            "xAxis": {"type": "time", "axisLabel": {"hideOverlap": True}},
            "yAxis": {"type": "value", "min": "dataMin"},
            "series": [{"type": "line", "data": [], "smooth": True}],
        }
    )

    def update_chart(temperature: float):
        data = chart.options["series"][0]["data"]
        data.append(
            [time.time() * 1000, temperature]
        )  # ECharts time axis expects milliseconds
        if len(data) > 20:
            data.pop(0)
        chart.update()  # push updated options to the frontend

    subscription = sensor.subscribe(update_chart)
    chart.on(
        "delete", lambda: subscription.unsubscribe()
    )  # clean up on page close/reload


ui.run(root)
