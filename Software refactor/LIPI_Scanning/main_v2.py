from nicegui import ui

with ui.row():
    with ui.column():
        ui.label("Header?").classes("text-h1")
        ui.label("Hello NiceGUI")
    with ui.column():
        ui.markdown("# Big Footer")
        ui.label("Hello NiceGUI")

ui.run(native=True, fullscreen=True)