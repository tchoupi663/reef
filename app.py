import streamlit as st
import sys
import subprocess
import os
import re
from pathlib import Path
from ruamel.yaml import YAML
import time

# Import shared logic from reef.py
# We need to make sure the current directory is in path to import reef
sys.path.append(str(Path(__file__).parent.resolve()))
from reef import SchemaManager, update_yaml_config_from_schema, update_ini_inventory, load_current_config, BASE_DIR, ANSIBLE_DIR, GROUP_VARS_FILE, HOSTS_INI_FILE, SCRIPTS_DIR

# --- setup & config ---
st.set_page_config(
    page_title="REEF Manager",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for "Pretty" UI
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em; 
    }
    .stSuccess {
        background-color: #d1e7dd;
        color: #0f5132;
        padding: 1rem;
        border-radius: 8px;
    }
    .stError {
        background-color: #f8d7da;
        color: #842029;
        padding: 1rem;
        border-radius: 8px;
    }
    h1 {
        color: #0d6efd;
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.sidebar.title("🌊 REEF Manager")
    
    menu_options = [
        "Dashboard",
        "Configuration", 
        "Prerequisites Check", 
        "Deploy & Manage",
        "Documentation"
    ]
    
    selection = st.sidebar.radio("Navigation", menu_options)
    
    st.sidebar.markdown("---")
    status_color = "green" if GROUP_VARS_FILE.exists() else "red"
    st.sidebar.markdown(f"**Status**: :{status_color}[{'Ready' if GROUP_VARS_FILE.exists() else 'Not Configured'}]")

    if selection == "Dashboard":
        render_dashboard()
    elif selection == "Configuration":
        render_configuration()
    elif selection == "Prerequisites Check":
        render_prerequisites()
    elif selection == "Deploy & Manage":
        render_deploy()
    elif selection == "Documentation":
        render_docs()

def render_dashboard():
    st.title("Welcome to REEF")
    st.markdown("### PME Security Automation Manager")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("""
        **What is this?**
        
        REEF is a tool to automate the deployment of:
        - Wazuh Security Platform (SIEM)
        - Suricata (IDS)
        - Fail2Ban
        - UFW Firewall 
        """)
    
    with col2:
        if GROUP_VARS_FILE.exists():
            config = load_current_config()
            manager_ip = config.get('wazuh_manager_ip', 'Unknown')
            endpoint_count = config.get('endpoint_count', 0)
            
            st.metric("Manager IP", manager_ip)
            st.metric("Configured Agents", endpoint_count)
        else:
            st.warning("⚠️ Configuration missing. Please go to the Configuration tab.")

    st.image("https://images.unsplash.com/photo-1550751827-4bd374c3f58b?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80", caption="Cybersecurity Dashboard", use_container_width=True)

def render_configuration():
    st.title("Configuration")
    st.markdown("Configure your deployment variables below. Changes are saved to `group_vars/all.yml`.")

    schema_file = BASE_DIR / "config.schema.yml"
    schema_mgr = SchemaManager(schema_file)
    categories = schema_mgr.get_categories()
    current_config = load_current_config()
    
    with st.form("config_form"):
        form_data = {}
        
        for cat_name, variables in categories.items():
            st.subheader(cat_name)
            col1, col2 = st.columns(2)
            cols = [col1, col2]
            
            for index, var in enumerate(variables):
                var_name = var['name']
                desc = var['description']
                default_val = current_config.get(var_name, var.get('default'))
                var_type = var.get('type')
                
                # Determine input widget type
                valid_col = cols[index % 2]
                
                if var_type == 'boolean':
                    val = valid_col.checkbox(desc, value=bool(default_val), help=var_name)
                elif var_type == 'integer':
                    val = valid_col.number_input(desc, value=int(default_val) if default_val is not None else 0, help=var_name)
                elif var.get('allowed_values'):
                    options = var.get('allowed_values')
                    try:
                        idx = options.index(default_val) if default_val in options else 0
                    except:
                        idx = 0
                    val = valid_col.selectbox(desc, options, index=idx, help=var_name)
                else:
                    is_password = 'password' in var_name or 'secret' in var_name
                    val = valid_col.text_input(desc, value=str(default_val) if default_val else "", type="password" if is_password else "default", help=var_name)
                
                form_data[var_name] = val
        
        # Agents Configuration
        st.markdown("---")
        st.subheader("Agent Inventory")
        st.info("Agent IPs and Credentials for `hosts.ini` generation (Required for deployment).")
        
        submitted = st.form_submit_button("Save Configuration")
        
        if submitted:
            # Validate
            errors = []
            final_data = {}
            for var_name, value in form_data.items():
                # Find the var def
                var_def = next((v for cat in categories.values() for v in cat if v['name'] == var_name), None)
                if var_def:
                    valid, res = schema_mgr.validate(var_def, value)
                    if not valid:
                        errors.append(f"{var_name}: {res}")
                    else:
                        final_data[var_name] = res
            
            if errors:
                for err in errors:
                    st.error(err)
            else:
                if update_yaml_config_from_schema(final_data):
                    st.success("Configuration saved successfully!")
                    # Reload to reflect changes
                    time.sleep(1)
                    st.rerun()

    # Dynamic Agent Input (Outside Main Config Form to allow dynamic rendering based on saved count)
    if GROUP_VARS_FILE.exists():
        current_config = load_current_config() # Reload fresh
        count = current_config.get('endpoint_count', 0)
        
        if count > 0:
            st.markdown("### Agent Details")
            with st.form("agents_form"):
                agents_data = []
                
                for i in range(count):
                    st.markdown(f"**Agent {i+1}**")
                    c1, c2, c3 = st.columns(3)
                    ip = c1.text_input(f"IP Address ##{i}", key=f"agent_ip_{i}")
                    user = c2.text_input(f"SSH User ##{i}", value="root", key=f"agent_user_{i}")
                    pw = c3.text_input(f"SSH Password ##{i}", type="password", key=f"agent_pw_{i}")
                    agents_data.append({'ip': ip, 'user': user, 'password': pw})
                
                st.markdown("---")
                mgr_user = st.text_input("Manager SSH User", value="root")
                mgr_pass = st.text_input("Manager SSH Password", type="password")
                
                if st.form_submit_button("Update Inventory (hosts.ini)"):
                    mgr_ip = current_config.get('wazuh_manager_ip')
                    if update_ini_inventory(mgr_ip, mgr_user, mgr_pass, agents_data):
                        st.success("Inventory updated!")

def render_prerequisites():
    st.title("Prerequisites Check")
    
    mode = st.radio("Check Mode", ["Check Local Machine", "Check Remote Target"])
    
    target_ip = None
    target_user = "root"
    
    if mode == "Check Remote Target":
        c1, c2 = st.columns(2)
        target_ip = c1.text_input("Remote IP")
        target_user = c2.text_input("Remote User", value="root")
    
    if st.button("Run Check"):
        st.info("Running check... Output will stream below.")
        with st.container():
            script_path = SCRIPTS_DIR / "prerequisites-check.sh"
            
            cmd = f"bash {script_path}"
            if target_ip:
                ssh_opts = "-o ControlMaster=auto -o ControlPersist=60s -o ControlPath=/tmp/reef-ssh-%r@%h:%p"
                remote_path = "/tmp/check.sh"
                scp_cmd = f"scp {ssh_opts} {script_path} {target_user}@{target_ip}:{remote_path}"
                run_shell_stream(scp_cmd)
                cmd = f"ssh {ssh_opts} -t {target_user}@{target_ip} 'sudo bash {remote_path}; sudo rm {remote_path}'"

            run_shell_stream(cmd)

def render_deploy():
    st.title("Deploy & Manage")
    
    tab1, tab2 = st.tabs(["Deploy", "Emergency Cleanup"])
    
    with tab1:
        st.warning("⚠️ This will overwrite existing configurations on target servers.")
        
        # Role Toggles
        st.subheader("Enabled Components")
        roles_dir = ANSIBLE_DIR / "roles"
        if roles_dir.exists():
            all_roles = sorted([d.name for d in roles_dir.iterdir() if d.is_dir()])
        else:
            all_roles = []
            
        current_config = load_current_config()
        enabled = current_config.get('enabled_roles', all_roles)
        
        selected_roles = st.multiselect("Select Roles to Deploy", all_roles, default=enabled)
        
        if st.button("Save Role Selection"):
            current_config['enabled_roles'] = selected_roles
            update_yaml_config_from_schema(current_config)
            st.toast("Roles updated!")

        st.markdown("---")
        
        if st.button("🚀 Start Deployment", type="primary"):
            playbook = ANSIBLE_DIR / "playbooks" / "experimental.yml"
            inventory = HOSTS_INI_FILE
            cmd = f"ansible-playbook {playbook} -i {inventory}"
            
            st.write("Starting Ansible Playbook...")
            run_shell_stream(cmd)
                
    with tab2:
        st.error("DANGER ZONE: This will remove all components.")
        if st.button("🔥 Run Cleanup", type="primary"):
             playbook = ANSIBLE_DIR / "playbooks" / "experimental.yml"
             inventory = HOSTS_INI_FILE
             # cleanup tag
             cmd = f"ansible-playbook {playbook} -i {inventory} -e '{{\"enabled_roles\": [\"cleanup\"]}}'"
             run_shell_stream(cmd)

def render_docs():
    st.title("Documentation")
    docs_dir = BASE_DIR / "docs"
    docs = list(docs_dir.glob("*.md")) + [BASE_DIR / "README.md"]
    
    doc = st.selectbox("Select Document", [d.name for d in docs])
    
    selected_path = next((d for d in docs if d.name == doc), None)
    if selected_path:
        st.markdown(selected_path.read_text())

def run_shell_stream(command):
    """Run command and stream output to Streamlit."""
    process = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        executable='/bin/zsh'
    )
    
    # Create an empty placeholder
    output_placeholder = st.empty()
    output_lines = []
    
    # Read output line by line
    for line in iter(process.stdout.readline, ""):
        output_lines.append(line)
        # Updates code block with full path so far - effectively streaming
        # keep last 1000 chars or lines to prevent explosion?
        text = "".join(output_lines[-50:]) # Keep last 50 lines for view
        output_placeholder.code(text, language="bash")
    
    process.wait()
    
    if process.returncode == 0:
        st.success("Command completed successfully.")
    else:
        st.error(f"Command failed with exit code {process.returncode}")
    
    return process.returncode

if __name__ == "__main__":
    main()
