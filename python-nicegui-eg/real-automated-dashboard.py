import subprocess

from nicegui import ui


def run_task(script):
    subprocess.run(["python", script])
    ui.notify(f"{script} finished")


with ui.card():
    ui.label("Automation Dashboard")
    ui.button("Clean Files", on_click=lambda: run_task("clean.py"))
    ui.button("Backup Data", on_click=lambda: run_task("backup.py"))
    ui.button("Generate Reports", on_click=lambda: run_task("report.py"))

ui.run()
