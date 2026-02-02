from nicegui import ui
from reef.manager.core import SchemaManager, update_yaml_config_from_schema, update_ini_inventory, load_current_config, BASE_DIR, GROUP_VARS_FILE, HOSTS_INI_FILE, generate_terraform_vm_config, run_terraform_apply, get_manager_credentials_from_inventory, get_inventory_hosts
from reef.manager.ui_utils import page_header, card_style, app_state
import asyncio
import re

def show_configuration():
    page_header("Settings", "Configure your security environment")
    
    schema_file = BASE_DIR / "config.schema.yml"
    schema_mgr = SchemaManager(schema_file)
    categories = schema_mgr.get_categories()
    current_config = load_current_config()
    
    # Store form inputs
    form_inputs = {}

    async def save_config():
        final_data = {}
        errors = []
        
        for var_name, input_elem in form_inputs.items():
            value = input_elem.value
            
            # Find var def
            var_def = next((v for cat in categories.values() for v in cat if v['name'] == var_name), None)
            if var_def:
                valid, res = schema_mgr.validate(var_def, value)
                if not valid:
                    errors.append(f"{var_name}: {res}")
                else:
                    final_data[var_name] = res
        
        if errors:
            for err in errors:
                ui.notify(err, type='negative')
        else:
            if update_yaml_config_from_schema(final_data):
                ui.notify("Configuration saved successfully!", type='positive')
                # Refresh page to update the Agent Inventory section based on new config
                ui.timer(1.0, lambda: ui.run_javascript('window.location.reload()'), once=True)

    # --- Main Config Form ---
    with ui.column().classes('w-full gap-8'):
        
        for cat_name, variables in categories.items():
            with ui.column().classes(card_style() + ' w-full'):
                ui.label(cat_name).classes('text-xl font-bold text-slate-200 mb-4')
                
                with ui.grid(columns=2).classes('w-full gap-6'):
                    for var in variables:
                        var_name = var['name']
                        desc = var['description']
                        default_val = current_config.get(var_name, var.get('default'))
                        var_type = var.get('type')
                        
                        if var_type == 'boolean':
                            form_inputs[var_name] = ui.checkbox(desc, value=bool(default_val)).classes('text-slate-300')
                        
                        elif var_type == 'integer':
                            form_inputs[var_name] = ui.number(desc, value=int(default_val) if default_val is not None else 0).classes('w-full text-slate-300')
                        
                        elif var.get('allowed_values'):
                            options = var.get('allowed_values')
                            form_inputs[var_name] = ui.select(options, value=default_val, label=desc).classes('w-full text-slate-300')
                        
                        else:
                            is_password = 'password' in var_name or 'secret' in var_name
                            form_inputs[var_name] = ui.input(desc, value=str(default_val) if default_val else "", password=is_password).classes('w-full text-slate-300')

        ui.button("Save Settings", on_click=save_config).classes('bg-indigo-600 w-full')
    
    # --- Infrastructure Provisioning Section ---
    ui.separator().classes('my-8 bg-slate-700')
    
    with ui.column().classes(card_style() + ' w-full'):
        ui.label("Infrastructure Provisioning").classes('text-xl font-bold text-slate-200 mb-2')
        ui.markdown("Create new Virtual Machines to add to your inventory.").classes('text-slate-400 mb-6')
        
        with ui.grid(columns=3).classes('w-full gap-4'):
             vm_count_sel = ui.select([1, 2, 3, 4, 5], value=1, label='Number of VMs').classes('w-full text-slate-300')
             vm_os_sel = ui.select(['ubuntu-22.04', 'debian-11'], value='ubuntu-22.04', label='Operating System').classes('w-full text-slate-300')
             vm_pw_in = ui.input(label='VM SSH Password', password=True).classes('w-full text-slate-300')
        
        vm_prefix_in = ui.input(label='VM Name Prefix', value='vm', placeholder='e.g., node').classes('w-full text-slate-300')
        
        prov_log = ui.log().classes('w-full h-40 bg-slate-900 font-mono text-xs p-4 rounded-xl border border-white/5 hidden')
        
        async def run_provision():
            prov_log.classes(remove='hidden')
            prov_log.clear()
            
            try:
                count = int(vm_count_sel.value)
                os_choice = vm_os_sel.value
                password = vm_pw_in.value or 'ubuntu'
                prefix = vm_prefix_in.value or 'vm'
                
                prov_log.push(f"[PROVISION] Preparing to create {count} VMs ({os_choice})...")
                
                # Build Specs
                vm_specs = []
                for i in range(count):
                    name = f"{prefix}-{i+1}"
                    vm_specs.append({
                        'name': name,
                        'ssh_password': password,
                        'os': os_choice
                    })
                
                # Get Manager Creds
                manager_ip, manager_ssh_user, manager_ssh_password, manager_ssh_key = await asyncio.to_thread(get_manager_credentials_from_inventory)
                
                if not manager_ip:
                     prov_log.push("[ERROR] Manager IP not found in hosts.ini. Please configure manually first.")
                     return

                # Generate Terraform
                gen_result = await asyncio.to_thread(generate_terraform_vm_config, vm_specs, manager_ip, manager_ssh_user, manager_ssh_password, manager_ssh_key)
                
                if not gen_result.get('success'):
                    prov_log.push(f"[ERROR] Terraform Config Gen Failed: {gen_result.get('message')}")
                    return
                
                prov_log.push("[PROVISION] Terraform configuration generated. Applying...")
                
                # Apply Terraform
                def log_wrapper(msg):
                    prov_log.push(msg.strip())
                
                tf_result = await asyncio.to_thread(
                    run_terraform_apply,
                    gen_result.get('terraform_dir'),
                    log_wrapper,
                    gen_result.get('manager_ssh_password'),
                    gen_result.get('manager_ip'),
                    gen_result.get('manager_ssh_user'),
                    manager_ssh_key
                )
                
                if tf_result.get('success'):
                    prov_log.push("[PROVISION] Infrastructure provisioning successful.")
                    
                    # Update Inventory
                    tf_output = tf_result.get('output', '')
                    ip_matches = re.findall(r'(\S+)_ip\s*=\s*"([^"]+)"', tf_output)
                    
                    if ip_matches:
                        prov_log.push(f"[INVENTORY] Found {len(ip_matches)} new IPs. Updating hosts.ini...")
                        
                        current_hosts = await asyncio.to_thread(get_inventory_hosts)
                        
                        # Prepare data for update
                        curr_mgr_ip, curr_mgr_user, curr_mgr_pw, curr_mgr_key = await asyncio.to_thread(get_manager_credentials_from_inventory)
                        new_agents_data = [h for h in current_hosts if h['ip'] != curr_mgr_ip]
                        
                        for vm_key, vm_ip in ip_matches:
                            clean_name = vm_key.replace('_ip', '')
                            user_name = re.sub(r'[^a-z0-9-]', '', clean_name.lower()) or 'ubuntu'
                            
                            # Construct ProxyCommand for nested VM access
                            proxy_cmd = ""
                            if manager_ssh_key:
                                 proxy_cmd = f'-o ProxyCommand="ssh -W %h:%p -i {manager_ssh_key} -o StrictHostKeyChecking=no {manager_ssh_user}@{manager_ip}"'
                            elif manager_ssh_password:
                                 proxy_cmd = f'-o ProxyCommand="sshpass -p \'{manager_ssh_password}\' ssh -W %h:%p -o StrictHostKeyChecking=no {manager_ssh_user}@{manager_ip}"'

                            entry = {
                                'ip': vm_ip,
                                'user': user_name,
                                'password': 'ubuntu',
                                'key': '',
                                'type': 'vm',
                                'hypervisor': manager_ip,
                                'vm_name': clean_name,
                                'ansible_ssh_common_args': proxy_cmd
                            }
                             # Update existing or append
                            existing = next((a for a in new_agents_data if a['ip'] == vm_ip), None)
                            if existing:
                                existing.update(entry)
                            else:
                                new_agents_data.append(entry)
                        
                        success = await asyncio.to_thread(update_ini_inventory, curr_mgr_ip, curr_mgr_user, curr_mgr_pw, curr_mgr_key, new_agents_data)
                        
                        if success:
                             prov_log.push("[INVENTORY] hosts.ini updated.")
                             ui.notify("VMs created and inventory updated!", type='positive')
                             ui.timer(2.0, lambda: ui.run_javascript('window.location.reload()'), once=True)
                        else:
                             prov_log.push("[ERROR] Failed to update hosts.ini")
                    else:
                        prov_log.push("[WARNING] No IPs found in Terraform output.")
                
                else:
                    prov_log.push(f"[ERROR] Terraform Apply Failed: {tf_result.get('message')}")
                    ui.notify("Provisioning failed.", type='negative')

            except Exception as e:
                prov_log.push(f"[CRITICAL] {e}")
                ui.notify(f"Error: {e}", type='negative')
        
        ui.button("Provision VMs", on_click=run_provision).classes('bg-indigo-600')

    # --- Agents Inventory Section ---
    ui.separator().classes('my-8 bg-slate-700')
    
    with ui.column().classes(card_style() + ' w-full'):
        ui.label("Computer Inventory").classes('text-xl font-bold text-slate-200 mb-2')
        ui.markdown("List the computers you want to protect. You need to provide their IP address and login credentials so the system can install the necessary software.").classes('text-slate-400 mb-6')

        if GROUP_VARS_FILE.exists():
            # Reload to get fresh count if it changed
            fresh_config = load_current_config()
            count = fresh_config.get('endpoint_count', 0)
            
            # Helper to parse current inventory
            existing_agents = []
            existing_manager = {'user': 'root', 'password': '', 'key': ''}

            if HOSTS_INI_FILE.exists():
                content = HOSTS_INI_FILE.read_text()
                lines = content.splitlines()
                current_section = None
                
                for line in lines:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    if line.startswith('['):
                        current_section = line.strip('[]')
                        continue
                    
                    parts = line.split()
                    if not parts:
                        continue

                    # Parse common ansible vars
                    ip = parts[0]
                    user = "root"
                    pw = ""
                    key = ""
                    
                    for p in parts[1:]:
                        if p.startswith("ansible_user="):
                            user = p.split("=", 1)[1]
                        elif p.startswith("ansible_ssh_pass=") or p.startswith("ansible_password="):
                            pw = p.split("=", 1)[1]
                        elif p.startswith("ansible_ssh_private_key_file="):
                            key = p.split("=", 1)[1]

                    if current_section in ['agents', 'wazuh_agents']:
                        # Capture extra vars
                        extra = {}
                        for p in parts[1:]:
                            if '=' in p and not any(p.startswith(k) for k in ["ansible_user=", "ansible_ssh_pass=", "ansible_password=", "ansible_ssh_private_key_file="]):
                                k, v = p.split('=', 1)
                                extra[k] = v
                                
                        agent_data = {'ip': ip, 'user': user, 'password': pw, 'key': key}
                        agent_data.update(extra)
                        existing_agents.append(agent_data)
                    elif current_section == 'security_server':
                        existing_manager['user'] = user
                        existing_manager['password'] = pw
                        existing_manager['key'] = key

            if count > 0:
                agent_inputs = []
                
                # Filter out VMs from the manual editing slots list so they don't take up "Computer 1", "Computer 2" slots
                manual_agents = [a for a in existing_agents if a.get('type') != 'vm']

                with ui.column().classes('gap-4 w-full'):
                    for i in range(count):
                        ui.label(f"Computer {i+1}").classes('font-bold text-slate-300 mt-2')
                        
                        def_ip = manual_agents[i]['ip'] if i < len(manual_agents) else ""
                        def_user = manual_agents[i]['user'] if i < len(manual_agents) else "root"
                        def_pw = manual_agents[i]['password'] if i < len(manual_agents) else ""
                        def_key = manual_agents[i]['key'] if i < len(manual_agents) else ""
                        
                        with ui.grid(columns=4).classes('w-full gap-4'):
                            ip_in = ui.input("IP Address", value=def_ip).classes('w-full')
                            user_in = ui.input("SSH User", value=def_user).classes('w-full')
                            pw_in = ui.input("SSH Password", value=def_pw, password=True).classes('w-full')
                            key_in = ui.input("SSH Key Path", value=def_key).classes('w-full')
                            
                            agent_inputs.append({'ip': ip_in, 'user': user_in, 'pw': pw_in, 'key': key_in})
                    
                    # Show Read-only VMs if any
                    vm_agents = [a for a in existing_agents if a.get('type') == 'vm']
                    if vm_agents:
                         ui.separator().classes('my-4 bg-white/10')
                         ui.label("Provisioned Virtual Machines (Managed Automatically)").classes('text-slate-400 font-bold mb-2')
                         
                         with ui.grid(columns=4).classes('w-full gap-4 opacity-60'):
                             for vm in vm_agents:
                                 ui.input("IP Address", value=vm['ip']).classes('w-full').props('readonly')
                                 ui.input("SSH User", value=vm['user']).classes('w-full').props('readonly')
                                 ui.input("Hypervisor", value=vm.get('hypervisor', 'Unknown')).classes('w-full').props('readonly')
                                 ui.label("Managed by Terraform").classes('text-slate-500 text-xs self-center')

                    ui.separator().classes('my-4 bg-white/10')
                    
                    # Manager Credentials
                    ex_mgr_user = existing_manager['user']
                    ex_mgr_pw = existing_manager['password']
                    ex_mgr_key = existing_manager['key']
                        
                    with ui.grid(columns=4).classes('w-full gap-4'):
                        mgr_user_in = ui.input("Security Server User", value=ex_mgr_user).classes('w-full')
                        mgr_pass_in = ui.input("Security Server Password", value=ex_mgr_pw, password=True).classes('w-full')
                        mgr_key_in = ui.input("Security Server Key Path", value=ex_mgr_key).classes('w-full')

                    def save_inventory():
                        # Collect data
                        agents_data = []
                        for row in agent_inputs:
                            a_ip = row['ip'].value
                            a_user = row['user'].value
                            a_pw = row['pw'].value
                            a_key = row['key'].value
                            
                            entry = {
                                'ip': a_ip,
                                'user': a_user,
                                'password': a_pw,
                                'key': a_key
                            }
                            
                            # Auto-add ProxyCommand for nested VMs (192.168.122.x)
                            if a_ip and a_ip.startswith("192.168.122."):
                                mgr_ip = fresh_config.get('wazuh_manager_ip')
                                m_user = mgr_user_in.value or 'root'
                                m_pw = mgr_pass_in.value
                                m_key = mgr_key_in.value
                                
                                proxy_cmd = ""
                                if m_key:
                                     proxy_cmd = f'-o ProxyCommand="ssh -W %h:%p -i {m_key} -o StrictHostKeyChecking=no {m_user}@{mgr_ip}"'
                                elif m_pw:
                                     # Note: sshpass usage might be tricky in pure config string without proper escaping, 
                                     # but we try best effort or rely on ssh key preference.
                                     proxy_cmd = f'-o ProxyCommand="sshpass -p \'{m_pw}\' ssh -W %h:%p -o StrictHostKeyChecking=no {m_user}@{mgr_ip}"'
                                
                                if proxy_cmd:
                                    entry['ansible_ssh_common_args'] = proxy_cmd

                            agents_data.append(entry)
                        
                        # Add VMs back to the list so they are not lost
                        vm_agents_to_save = [a for a in existing_agents if a.get('type') == 'vm']
                        agents_data.extend(vm_agents_to_save)

                        mgr_ip = fresh_config.get('wazuh_manager_ip')
                        if update_ini_inventory(mgr_ip, mgr_user_in.value, mgr_pass_in.value, mgr_key_in.value, agents_data):
                            ui.notify("Inventory updated!", type='positive')

                    ui.button("Save Computer List", on_click=save_inventory).classes('bg-emerald-600 w-full mt-4')
            else:
                 ui.label("Set 'endpoint_count' > 0 in configuration above to configure agents.").classes('text-amber-400')
