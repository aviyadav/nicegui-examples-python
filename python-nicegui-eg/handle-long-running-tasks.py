import asyncio

from nicegui import ui


async def sync_data():
    for i in range(10):
        await asyncio.sleep(1)
        progress.value += 0.1
    ui.notify("Data sync complete")


progress = ui.linear_progress(value=0)
ui.button("Start Sync", on_click=sync_data)

ui.run()
