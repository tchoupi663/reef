from nicegui import ui
from manager.core import GROUP_VARS_FILE, HOSTS_INI_FILE, load_current_config
from manager.ui_utils import page_header, card_style, status_badge

def show_dashboard():
    page_header("Dashboard", "Security Infrastructure Manager")

    ui.markdown("""
    <p style="color: #94a3b8; font-size: 1.1em; line-height: 1.6; margin-top: -10px;">
    REEF simplifies the deployment of your security stack. 
    Automate SIEM, IDS, and network defenses with a unified management interface.
    </p>
    """).classes('mb-8')

    if not GROUP_VARS_FILE.exists():
        with ui.card().classes('w-full bg-amber-500/10 border-amber-500/20'):
            with ui.row().classes('items-center gap-4'):
                ui.icon('warning', size='lg').classes('text-amber-500')
                ui.label("Configuration missing. Please go to the Configuration tab to initialize the system.").classes('text-amber-500 text-lg')
        return

    # Load data
    config = load_current_config()
    manager_ip = config.get('wazuh_manager_ip', 'Unknown')
    enabled_roles = config.get('enabled_roles', [])
        
    # Count agents
    agent_ips = []
    if HOSTS_INI_FILE.exists():
        content = HOSTS_INI_FILE.read_text()
        lines = content.splitlines()
        in_agents = False
        for line in lines:
            if line.strip() == "[agents]" or line.strip() == "[wazuh_agents]":
                in_agents = True
                continue
            if line.strip().startswith("[") and line.strip() not in ["[agents]", "[wazuh_agents]"]:
                in_agents = False
            
            if in_agents and line.strip() and not line.strip().startswith("#"):
                parts = line.strip().split()
                if parts:
                    agent_ips.append(parts[0])

    agent_count = len(agent_ips)

    # Grid Layout
    with ui.grid(columns=2).classes('w-full gap-6'):
        
        # Core Infrastructure Card
        with ui.column().classes(card_style()):
            ui.label('Core Infrastructure').classes('text-slate-400 font-bold mb-4 border-b border-white/10 pb-2 w-full')
            
            with ui.column().classes('gap-6 w-full'):
                
                # Status Row
                with ui.row().classes('w-full justify-between items-center'):
                    with ui.column().classes('gap-0'):
                        ui.label('SYSTEM STATUS').classes('text-xs text-slate-500 font-bold')
                        status_badge(HOSTS_INI_FILE.exists(), "Active", "Pending Setup")
                    
                    with ui.column().classes('gap-0 items-end'):
                        ui.label('MANAGER NODE').classes('text-xs text-slate-500 font-bold')
                        ui.label(manager_ip).classes('font-mono text-slate-300 bg-white/5 px-2 py-1 rounded')

                # Agents Box
                with ui.row().classes('w-full bg-sky-500/5 border border-sky-500/10 rounded-xl p-4 items-center gap-4'):
                    with ui.element('div').classes('flex items-center justify-center w-12 h-12 rounded-lg bg-sky-500 text-white text-2xl'):
                        ui.icon('monitor')
                    
                    with ui.column().classes('gap-0'):
                        ui.label(f'{agent_count} Agents').classes('text-slate-200 font-bold text-lg')
                        ui.label('Inventory Endpoints').classes('text-slate-400 text-sm')
                
                if agent_ips:
                    with ui.scroll_area().classes('w-full h-24 gap-1 grid grid-cols-2'):
                         for ip in agent_ips:
                             ui.label(f'• {ip}').classes('font-mono text-slate-500 text-xs')


        # Active Roles Card
        with ui.column().classes(card_style()):
            ui.label('Active Components').classes('text-slate-400 font-bold mb-4 border-b border-white/10 pb-2 w-full')
            
            with ui.grid(columns=2).classes('w-full gap-3 mb-6'):
                if enabled_roles:
                    for role in enabled_roles:
                        with ui.row().classes('bg-white/5 border border-white/5 rounded-lg p-2 items-center gap-2'):
                            ui.icon('check', size='xs').classes('text-emerald-400')
                            ui.label(role.replace("_", " ").title()).classes('text-slate-200 text-sm')
                else:
                    ui.label('No roles enabled.').classes('col-span-2 text-slate-500')

            ui.separator().classes('bg-white/10 mb-4')
            
            with ui.column().classes('gap-1'):
                ui.label('ENVIRONMENT INFO').classes('text-xs text-slate-500 font-bold mb-2')
                
                with ui.row().classes('gap-6'):
                    with ui.column().classes('gap-0'):
                        ui.label('Config File').classes('text-xs text-slate-400')
                        ui.label('group_vars/all.yml').classes('text-sm text-slate-300')
                    
                    with ui.column().classes('gap-0'):
                        ui.label('Inventory').classes('text-xs text-slate-400')
                        ui.label('hosts.ini').classes('text-sm text-slate-300')
