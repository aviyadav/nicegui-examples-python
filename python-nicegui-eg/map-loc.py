from nicegui import ui


def root():
    ui.sub_pages(
        {
            "/": table_page,
            "/map/{lat}/{lon}": map_page,
        }
    ).classes("w-full")


def table_page():
    ui.table(
        rows=[
            {"name": "New York", "lat": 40.7119, "lon": -74.0027},
            {"name": "London", "lat": 51.5074, "lon": -0.1278},
            {"name": "Tokyo", "lat": 35.6863, "lon": 139.7722},
            {"name": "Patna", "lat": 25.6139, "lon": 85.1312},
            {"name": "Bengaluru", "lat": 12.9716, "lon": 77.5946},
        ]
    ).on(
        "row-click",
        lambda e: ui.navigate.to(f"/map/{e.args[1]['lat']}/{e.args[1]['lon']}"),
    )


def map_page(lat: float, lon: float):
    ui.leaflet(center=(lat, lon), zoom=10)
    ui.link("Back to table", "/")


ui.run(root)
