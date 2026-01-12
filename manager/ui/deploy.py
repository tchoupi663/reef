from nicegui import ui
import os
import asyncio
from pathlib import Path
from manager.core import ANSIBLE_DIR, HOSTS_INI_FILE, load_current_config, update_yaml_config_from_schema
from manager.ui_utils import page_header, card_style, async_run_command

def show_deploy():
    page_header("Deploy & Manage", "Execute playbooks and manage lifecycle")
    
    with ui.tabs().classes('w-full text-slate-300') as tabs:
        tab_deploy = ui.tab('Deploy')
        tab_cleanup = ui.tab('Emergency Cleanup')

    with ui.tab_panels(tabs, value=tab_deploy).classes('w-full bg-transparent'):
        
        # --- DEPLOY TAB ---
        with ui.tab_panel(tab_deploy):
            with ui.column().classes('w-full gap-6'):
                
                # Warning
                with ui.row().classes('w-full bg-amber-500/10 border border-amber-500/20 p-4 rounded-xl items-center gap-4'):
                    ui.icon('warning', size='md').classes('text-amber-500')
                    ui.label("This will overwrite existing configurations on target servers.").classes('text-amber-500 font-bold')

                # Roles Selection
                with ui.column().classes(card_style() + ' w-full'):
                    ui.label("Enabled Components").classes('text-xl font-bold text-slate-200 mb-4')
                    
                    roles_dir = ANSIBLE_DIR / "roles"
                    all_roles = sorted([d.name for d in roles_dir.iterdir() if d.is_dir()]) if roles_dir.exists() else []
                    current_config = load_current_config()
                    enabled = current_config.get('enabled_roles', all_roles)
                    
                    selected_roles = []
                    
                    with ui.grid(columns=3).classes('w-full gap-4'):
                        for role in all_roles:
                            chk = ui.checkbox(role, value=(role in enabled)).classes('text-slate-300')
                            selected_roles.append((role, chk))
                    
                    def save_roles():
                        new_enabled = [r for r, c in selected_roles if c.value]
                        current_config['enabled_roles'] = new_enabled
                        if update_yaml_config_from_schema(current_config):
                            ui.notify("Roles updated!", type='positive')
                            
                    ui.button("Save Role Selection", on_click=save_roles).classes('mt-4 bg-slate-700')

                # Deployment Action
                with ui.column().classes(card_style() + ' w-full'):
                    btn_deploy = ui.button("🚀 Start Deployment", on_click=lambda: run_deployment()).classes('bg-indigo-600 w-full py-4 text-lg')
                    deploy_log = ui.log().classes('w-full h-64 bg-slate-900 font-mono text-xs p-4 rounded-xl border border-white/10 mt-4')

                    credentials_container = ui.column().classes('w-full mt-4 hidden')

            async def run_deployment():
                deploy_log.clear()
                credentials_container.classes('hidden')
                credentials_container.clear()
                btn_deploy.disable()
                
                playbook = ANSIBLE_DIR / "playbooks" / "experimental.yml"
                inventory = HOSTS_INI_FILE
                cmd = f"ansible-playbook {playbook} -i {inventory}"
                
                deploy_log.push("Starting Ansible Playbook...")
                
                # We need to capture output to parse password, so let's do a custom run or just reuse async_run
                # For simplicity, we use async_run but we might need a way to capture the text if we want to parse it *after* 
                # or during. ui.log stores text, but accessing it programmatically isn't direct.
                # Let's use a capture list.
                captured_lines = []
                
                process = await asyncio.create_subprocess_shell(
                    cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT,
                    executable='/bin/zsh'
                )

                while True:
                    line = await process.stdout.readline()
                    if not line:
                        break
                    text = line.decode().strip()
                    deploy_log.push(text)
                    captured_lines.append(text)

                await process.wait()
                
                if process.returncode == 0:
                    ui.notify("Deployment Successful!", type='positive')
                    # Parse output
                    full_output = "\n".join(captured_lines)
                    check_credentials(full_output)
                else:
                    ui.notify(f"Deployment failed (Exit {process.returncode})", type='negative')
                
                btn_deploy.enable()

            def check_credentials(output):
                # Attempt to retrieve credentials
                config = load_current_config()
                manager_ip = config.get('wazuh_manager_ip', '<manager_ip>')
                
                password = None
                pass_file = Path(os.environ.get('HOME')) / 'Downloads' / 'wazuh-admin-password.txt'
                
                import re
                match = re.search(r'"admin",\s+"([^"]+)"', output)
                if match:
                    password = match.group(1)
                elif pass_file.exists():
                     password = pass_file.read_text().strip().splitlines()[0] if pass_file.read_text().strip() else None
                
                # Only show if retrieved
                if password:
                    credentials_container.classes(remove='hidden')
                    with credentials_container:
                        with ui.column().classes('w-full bg-emerald-500/10 border border-emerald-500/30 p-6 rounded-xl'):
                            ui.label("🚀 System Operational").classes('text-emerald-400 text-xl font-bold mb-2')
                            ui.label("Your security stack is up and running.").classes('text-slate-300 mb-4')
                            
                            with ui.column().classes('bg-black/30 p-4 rounded-lg w-full gap-2 border border-white/10'):
                                with ui.row().classes('gap-2'):
                                    ui.label("Dashboard:").classes('font-bold text-slate-400')
                                    ui.link(f"https://{manager_ip}", f"https://{manager_ip}", new_tab=True).classes('text-sky-400 font-bold')
                                
                                with ui.row().classes('gap-2'):
                                    ui.label("Username:").classes('font-bold text-slate-400')
                                    ui.label("admin").classes('font-mono text-slate-200 bg-white/10 px-1 rounded')

                                with ui.row().classes('gap-2'):
                                    ui.label("Password:").classes('font-bold text-slate-400')
                                    ui.label(password).classes('font-mono text-rose-300 font-bold bg-white/10 px-1 rounded')
                            
                            ui.label("Note: Accept the self-signed certificate warning.").classes('text-slate-500 text-sm mt-2 italic')


        # --- CLEANUP TAB ---
        with ui.tab_panel(tab_cleanup):
            with ui.column().classes('w-full gap-6'):
                with ui.row().classes('w-full bg-rose-500/10 border border-rose-500/20 p-4 rounded-xl items-center gap-4'):
                    ui.icon('dangerous', size='md').classes('text-rose-500')
                    ui.label("DANGER ZONE: This will remove all components.").classes('text-rose-500 font-bold')
                
                cleanup_log = ui.log().classes('w-full h-64 bg-slate-900 font-mono text-xs p-4 rounded-xl border border-white/10')
                
                async def run_cleanup():
                    cleanup_log.clear()
                    playbook = ANSIBLE_DIR / "playbooks" / "experimental.yml"
                    inventory = HOSTS_INI_FILE
                    cmd = f"ansible-playbook {playbook} -i {inventory} -e '{{\"enabled_roles\": [\"cleanup\"]}}'"
                    await async_run_command(cmd, cleanup_log)

                ui.button("🔥 Run Cleanup", on_click=lambda: run_cleanup()).classes('bg-rose-600 w-full py-4 text-lg')
