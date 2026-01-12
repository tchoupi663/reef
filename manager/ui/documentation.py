from nicegui import ui
from manager.core import BASE_DIR
from manager.ui_utils import page_header

def show_documentation():
    page_header("Documentation", "Guides and References")
    
    docs_dir = BASE_DIR / "docs"
    
    # Simple ToC or just list files
    if docs_dir.exists():
        files = sorted(list(docs_dir.glob("*.md")))
        
        with ui.row().classes('w-full h-full'):
            # Sidebar for files
            with ui.column().classes('w-1/4 pr-4 border-r border-white/10'):
                ui.label("Files").classes('font-bold text-slate-400 mb-2')
                
                selected_content = ui.markdown().classes('w-full')
                
                # Default to README if exists
                readme = BASE_DIR / "README.md"
                if readme.exists():
                     selected_content.content = readme.read_text()

                def load_doc(path):
                    selected_content.content = path.read_text()

                if readme.exists():
                    ui.button("README", on_click=lambda p=readme: load_doc(p)).props('flat').classes('text-left w-full text-slate-300')

                for f in files:
                    ui.button(f.stem, on_click=lambda p=f: load_doc(p)).props('flat').classes('text-left w-full text-slate-300')
            
            # Content Area
            with ui.scroll_area().classes('w-3/4 pl-4 h-[calc(100vh-200px)]'):
                selected_content
    else:
        ui.label("No documentation found.").classes('text-slate-500')
