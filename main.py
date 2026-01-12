import sys
from pathlib import Path
from nicegui import ui

# Ensure path is set up (similar to original app.py)
current_dir = str(Path(__file__).parent.resolve())
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import Pages
from manager.ui.dashboard import show_dashboard
from manager.ui.configuration import show_configuration
from manager.ui.prerequisites import show_prerequisites
from manager.ui.deploy import show_deploy
from manager.ui.documentation import show_documentation

# --- App Layout & State ---

@ui.page('/')
def main_page():
    # Global Style
    ui.add_head_html("""
    <style>
        body { background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%); }
    </style>
    """)
    ui.colors(primary='#4f46e5', secondary='#06b6d4', accent='#111827', dark='#111827')

    # Sidebar
    with ui.left_drawer(value=True).classes('bg-slate-900 border-r border-white/5') as drawer:
        # Header
        with ui.row().classes('items-center gap-2 mb-8 mt-4'):
            ui.label('🌊').classes('text-2xl')
            with ui.column().classes('gap-0'):
                ui.label('REEF').classes('text-xl font-bold text-white tracking-widest')
                ui.label('Security Automation').classes('text-xs text-slate-400')
        
        # Navigation
        nav_items = [
            ('Dashboard', 'dashboard', show_dashboard),
            ('Configuration', 'settings', show_configuration),
            ('Prerequisites', 'check_circle', show_prerequisites),
            ('Deploy & Manage', 'rocket_launch', show_deploy),
            ('Documentation', 'menu_book', show_documentation),
        ]

    # Content Area
    content = ui.column().classes('w-full p-8 items-start')
    
    # Store button references to update state
    nav_buttons = {}

    def update_nav_visuals(active_title):
        for title, btn in nav_buttons.items():
            if title == active_title:
                # Active: brighter background, white text
                btn.classes(remove='text-slate-300 hover:bg-white/5 bg-transparent', add='bg-indigo-600/20 text-white')
            else:
                # Inactive: default text, transparent bg
                btn.classes(remove='bg-indigo-600/20 text-white', add='text-slate-300 hover:bg-white/5 bg-transparent')

    def navigate(title, func):
        content.clear()
        with content:
            func()
        update_nav_visuals(title)

    # Populate Drawer Navigation 
    with drawer:
        for title, icon, func in nav_items:
            # We use text-slate-300 by default (lighter than original slate-400 often used)
            # User asked for lighter, so maybe slate-300 or 200 is good. Let's use 300 base, 200 hover/active.
            btn = ui.button(title, icon=icon, on_click=lambda t=title, f=func: navigate(t, f)) \
                .props('flat align=left') \
                .classes('w-full text-slate-300 hover:text-white hover:bg-white/5 transition-all')
            nav_buttons[title] = btn

    # Initial Load
    navigate('Dashboard', show_dashboard)

ui.run(title='REEF Manager', dark=True, storage_secret='reef_secret')
