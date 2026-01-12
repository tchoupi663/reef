from nicegui import ui
import os
from datetime import datetime
from manager.core import ANSIBLE_DIR, HOSTS_INI_FILE, BASE_DIR
from manager.ui_utils import page_header, card_style, async_run_command

def show_prerequisites():
    page_header("Prerequisites Check", "Verify system requirements and connectivity")

    with ui.column().classes('w-full gap-6'):
        
        # Options Card
        with ui.column().classes(card_style() + ' w-full'):
            ui.label("Options").classes('font-bold text-slate-300 mb-4')
            
            with ui.row().classes('gap-8 items-center'):
                mode = ui.radio(["Local Machine", "Inventory Hosts"], value="Local Machine").props('inline')
                verbose = ui.checkbox("More Verbose (-vv)")

        # Action Button
        btn_run = ui.button("Run Check", on_click=lambda: run_prereqs()).classes('bg-indigo-600')
        
        # Logs
        log_view = ui.log().classes('w-full h-96 bg-slate-900 font-mono text-xs p-4 rounded-xl border border-white/10')

    async def run_prereqs():
        log_view.clear()
        btn_run.disable()
        
        playbook = ANSIBLE_DIR / "playbooks" / "prerequisites.yml"
        verbosity_flag = "-vv" if verbose.value else ""
        
        env = os.environ.copy()
        env["ANSIBLE_CONFIG"] = str(ANSIBLE_DIR / "ansible.cfg")
        
        # Log to file setup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = BASE_DIR / "logs" / f"prerequisites_{timestamp}.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        if mode.value == "Local Machine":
            cmd = f"ansible-playbook {playbook} --connection=local -i localhost, {verbosity_flag}"
        else:
            if not HOSTS_INI_FILE.exists():
                ui.notify(f"Inventory file not found at {HOSTS_INI_FILE}", type='negative')
                btn_run.enable()
                return
            cmd = f"ansible-playbook {playbook} -i {HOSTS_INI_FILE} {verbosity_flag}"
            
        await async_run_command(cmd, log_view)
        btn_run.enable()
