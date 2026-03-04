from nicegui import ui
import time

ui.label("Hello from python-nicegui-eg!")

def generate_report():
    time.sleep(2)
    return 'Report generated successfully'

def run_report():
    result = generate_report()
    ui.notify(result)

ui.button("Run Report", on_click=run_report)

ui.run()
