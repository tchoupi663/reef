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
current_dir = str(Path(__file__).parent.resolve())
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from reef import SchemaManager, update_yaml_config_from_schema, update_ini_inventory, load_current_config, BASE_DIR, ANSIBLE_DIR, GROUP_VARS_FILE, HOSTS_INI_FILE, SCRIPTS_DIR
except ImportError:
    # Fallback or retry if streamlit messed up imports
    import reef
    from reef import SchemaManager, update_yaml_config_from_schema, update_ini_inventory, load_current_config, BASE_DIR, ANSIBLE_DIR, GROUP_VARS_FILE, HOSTS_INI_FILE, SCRIPTS_DIR

# --- setup & config ---
st.set_page_config(
    page_title="REEF Manager",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for "Pretty" UI
# Custom CSS for "Pretty" UI
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }

    /* Dark Theme Background & Text */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
        color: #e2e8f0;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #f8fafc !important;
        font-weight: 700;
        letter-spacing: -0.02em;
    }

    /* Cards / Containers */
    .css-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .css-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2);
        border-color: rgba(99, 102, 241, 0.4);
    }
    
    /* Metrics */
    [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.03);
        padding: 1rem;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    [data-testid="stMetricLabel"] {
        color: #94a3b8;
    }
    [data-testid="stMetricValue"] {
        color: #38bdf8;
        font-weight: 700;
    }

    /* Buttons (General/Secondary) */
    .stButton>button {
        background: rgba(255, 255, 255, 0.05);
        color: #e2e8f0;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        height: 3em;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        background: rgba(255, 255, 255, 0.1);
        border-color: rgba(255, 255, 255, 0.2);
        color: white;
    }

    /* Primary Button (Active Navigation / Actions) */
    .stButton>button[kind="primary"] {
        background: linear-gradient(90deg, #4f46e5 0%, #06b6d4 100%);
        color: white;
        border: none;
        font-weight: 600;
        box-shadow: 0 4px 14px 0 rgba(0,118,255,0.39);
    }
    .stButton>button[kind="primary"]:hover {
        transform: scale(1.02);
        box-shadow: 0 6px 20px rgba(0,118,255,0.23);
        border: none;
    }
    
    /* Inputs */
    .stTextInput>div>div>input {
        background-color: rgba(15, 23, 42, 0.6);
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
    }
    .stTextInput>div>div>input:focus {
        border-color: #38bdf8;
        box-shadow: 0 0 0 1px #38bdf8;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: rgba(15, 23, 42, 0.95);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* Success/Error/Info Messages overhaul */
    .stSuccess, .stInfo, .stWarning, .stError {
        background: rgba(16, 185, 129, 0.1) !important;
        border: 1px solid rgba(16, 185, 129, 0.2) !important;
        color: #34d399 !important;
        border-radius: 12px;
    }
    .stError {
        background: rgba(239, 68, 68, 0.1) !important;
        border-color: rgba(239, 68, 68, 0.2) !important;
        color: #f87171 !important;
    }
    .stWarning {
         background: rgba(245, 158, 11, 0.1) !important;
         border-color: rgba(245, 158, 11, 0.2) !important;
         color: #fbbf24 !important;
    }
    .stInfo {
        background: rgba(59, 130, 246, 0.1) !important;
        border-color: rgba(59, 130, 246, 0.2) !important;
        color: #60a5fa !important;
    }
    
    /* Header Tweaks */
    [data-testid="stHeader"] {
        background: transparent !important;
    }
    
    /* Remove the "Deploy" button specifically */
    .stDeployButton {
        display: none !important;
    }
    
    /* Hide the hamburger menu (Main Menu) */
    #MainMenu {
        visibility: hidden;
    }
    
    /* Hide the footer */
    footer {
        visibility: hidden;
    }
    
</style>
""", unsafe_allow_html=True)

def main():
    if 'page' not in st.session_state:
        st.session_state.page = "Dashboard"
        
    with st.sidebar:
        st.title("🌊 REEF")
        st.markdown('<p style="color: #94a3b8; margin-top: -20px; font-size: 0.9em;">Security Automation</p>', unsafe_allow_html=True)
        st.markdown("---")
        
        # Navigation Buttons
        nav_options = [
            ("Dashboard", "📊"),
            ("Configuration", "⚙️"),
            ("Prerequisites Check", "✅"),
            ("Deploy & Manage", "🚀"),
            ("Documentation", "📚")
        ]
        
        for page_name, icon in nav_options:
            # Highlight active page button using type="primary" for the active one
            is_active = (st.session_state.page == page_name)
            btn_type = "primary" if is_active else "secondary"
            
            if st.button(f"{icon}  {page_name}", key=f"nav_{page_name}", use_container_width=True, type=btn_type):
                st.session_state.page = page_name
                st.rerun()

        st.markdown("---")
        status_color = "#34d399" if GROUP_VARS_FILE.exists() else "#f87171"
        status_text = "Ready" if GROUP_VARS_FILE.exists() else "Not Configured"
        st.markdown(f"""
        <div style="background: rgba(255,255,255,0.05); padding: 10px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1); text-align: center;">
            <div style="color: #94a3b8; font-size: 0.8em; text-transform: uppercase; letter-spacing: 1px;">System Status</div>
            <div style="color: {status_color}; font-weight: bold; margin-top: 4px;">● {status_text}</div>
        </div>
        """, unsafe_allow_html=True)

    # Main Content Router
    page = st.session_state.page
    
    if page == "Dashboard":
        render_dashboard()
    elif page == "Configuration":
        render_configuration()
    elif page == "Prerequisites Check":
        render_prerequisites()
    elif page == "Deploy & Manage":
        render_deploy()
    elif page == "Documentation":
        render_docs()

def render_dashboard():
    st.markdown("<h1>Welcome to <span style='background: linear-gradient(90deg, #4f46e5, #06b6d4); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>REEF</span></h1>", unsafe_allow_html=True)
    st.markdown("### Security Infrastructure Manager")
    
    st.markdown("---")
    
    col1, col2 = st.columns([1.5, 1])
    
    with col1:
        st.markdown("""
        <div class="css-card">
            <h3>Automate Your Security Stack</h3>
            <p style="color: #94a3b8; font-size: 1.1em; line-height: 1.6;">
                REEF simplifies the deployment of enterprise-grade security tools. 
                Deploy Wazuh, Suricata, and network defenses with a single click.
            </p>
            <br>
            <div style="display: flex; gap: 1rem; flex-wrap: wrap;">
                <span style="background: rgba(56, 189, 248, 0.1); color: #38bdf8; padding: 4px 12px; border-radius: 99px; font-size: 0.9em; border: 1px solid rgba(56, 189, 248, 0.2);">SIEM / Wazuh</span>
                <span style="background: rgba(168, 85, 247, 0.1); color: #a855f7; padding: 4px 12px; border-radius: 99px; font-size: 0.9em; border: 1px solid rgba(168, 85, 247, 0.2);">IDS / Suricata</span>
                <span style="background: rgba(16, 185, 129, 0.1); color: #34d399; padding: 4px 12px; border-radius: 99px; font-size: 0.9em; border: 1px solid rgba(16, 185, 129, 0.2);">Firewall / UFW</span>
                <span style="background: rgba(16, 185, 129, 0.1); color: #34d399; padding: 4px 12px; border-radius: 99px; font-size: 0.9em; border: 1px solid rgba(16, 185, 129, 0.2);">IPS /Fail2Ban</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        if GROUP_VARS_FILE.exists():
            config = load_current_config()
            manager_ip = config.get('wazuh_manager_ip', 'Unknown')
            endpoint_count = config.get('endpoint_count', 0)
            
            st.markdown(f"""
            <div class="css-card">
                <h4 style="margin-top:0; color: #94a3b8;">Infrastructure Overview</h4>
                <div style="margin-top: 1rem; display: flex; flex-direction: column; gap: 12px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 8px;">
                        <span style="color: #cbd5e1;">Manager IP</span>
                        <span style="font-family: monospace; color: #38bdf8;">{manager_ip}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="color: #cbd5e1;">Configured Agents</span>
                        <span style="color: #34d399; font-weight: bold;">{endpoint_count}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("⚠️ Configuration missing. Please go to the Configuration tab.")

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Feature Cards
    c1, c2, c3 = st.columns(3)
    with c1:
         st.markdown("""
        <div class="css-card" style="text-align: center; padding: 1.5rem;">
            <div style="font-size: 2em; margin-bottom: 10px;">⚙️</div>
            <h4 style="color: white; margin:0;">Configure</h4>
            <p style="color: #64748b; font-size: 0.9em;">Define variables and inventory</p>
        </div>
        """, unsafe_allow_html=True)
    with c2:
         st.markdown("""
        <div class="css-card" style="text-align: center; padding: 1.5rem;">
            <div style="font-size: 2em; margin-bottom: 10px;">✅</div>
            <h4 style="color: white; margin:0;">Verify</h4>
            <p style="color: #64748b; font-size: 0.9em;">Check prerequisites instantly</p>
        </div>
        """, unsafe_allow_html=True)
    with c3:
         st.markdown("""
        <div class="css-card" style="text-align: center; padding: 1.5rem;">
            <div style="font-size: 2em; margin-bottom: 10px;">🚀</div>
            <h4 style="color: white; margin:0;">Deploy</h4>
            <p style="color: #64748b; font-size: 0.9em;">Launch playbook with one click</p>
        </div>
        """, unsafe_allow_html=True)

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

    # Dynamic Agent Input
    if GROUP_VARS_FILE.exists():
        current_config = load_current_config() # Reload fresh
        count = current_config.get('endpoint_count', 0)
        
        # Helper to parse current inventory
        existing_agents = []
        existing_mgr_user = "root"
        existing_mgr_pass = ""
        
        if HOSTS_INI_FILE.exists():
            # Standard ConfigParser fails on Ansible inventories because they interpret lines starting with IP 
            # as keys without values, or have duplicate keys if multiple hosts define same vars inline in a way Python doesn't like.
            # We skip the strict parser and use the manual text parser below.
            pass 
        
        # Simple manual parser for Ansible INI since ConfigParser is strict
        if HOSTS_INI_FILE.exists():
            content = HOSTS_INI_FILE.read_text()
            lines = content.splitlines()
            in_agents = False
            for line in lines:
                line = line.strip()
                if line == "[wazuh_agents]":
                    in_agents = True
                    continue
                if line.startswith("[") and line != "[wazuh_agents]":
                    in_agents = False
                
                if in_agents and line and not line.startswith("#"):
                    parts = line.split()
                    ip = parts[0]
                    user = "root"
                    pw = ""
                    for p in parts[1:]:
                        if p.startswith("ansible_user="):
                            user = p.split("=")[1]
                        if p.startswith("ansible_ssh_pass="):
                            pw = p.split("=")[1]
                    existing_agents.append({'ip': ip, 'user': user, 'password': pw})

                # Manager check
                if "ansible_user=" in line and "wazuh_manager" in content: # Lazy check, ideally parse manager section
                     pass

        if count > 0:
            st.markdown("### Agent Details")
            with st.form("agents_form"):
                agents_data = []
                
                for i in range(count):
                    st.markdown(f"**Agent {i+1}**")
                    
                    # Defaults
                    def_ip = existing_agents[i]['ip'] if i < len(existing_agents) else ""
                    def_user = existing_agents[i]['user'] if i < len(existing_agents) else "root"
                    def_pw = existing_agents[i]['password'] if i < len(existing_agents) else ""
                    
                    c1, c2, c3 = st.columns(3)
                    ip = c1.text_input(f"IP Address ##{i}", value=def_ip, key=f"agent_ip_{i}")
                    user = c2.text_input(f"SSH User ##{i}", value=def_user, key=f"agent_user_{i}")
                    pw = c3.text_input(f"SSH Password ##{i}", value=def_pw, type="password", key=f"agent_pw_{i}")
                    agents_data.append({'ip': ip, 'user': user, 'password': pw})
                
                st.markdown("---")
                # Try to find manager user/pass (simplified)
                # Typically stored in [wazuh_manager] or [all:vars]
                # For now default to root/empty or what was there if we could parse it fully.
                # Let's simple-parse manager section too.
                ex_mgr_user = "root"
                ex_mgr_pw = ""
                if HOSTS_INI_FILE.exists():
                     content = HOSTS_INI_FILE.read_text()
                     lines = content.splitlines()
                     in_mgr = False
                     for line in lines:
                         if line.strip() == "[wazuh_manager]":
                             in_mgr = True
                             continue
                         if line.startswith("[") and line.strip() != "[wazuh_manager]":
                             in_mgr = False
                         
                         if in_mgr and line.strip() and not line.startswith("#"):
                             parts = line.split()
                             for p in parts:
                                 if p.startswith("ansible_user="):
                                     ex_mgr_user = p.split("=")[1]
                                 if p.startswith("ansible_ssh_pass="):
                                     ex_mgr_pw = p.split("=")[1]
                
                mgr_user = st.text_input("Manager SSH User", value=ex_mgr_user)
                mgr_pass = st.text_input("Manager SSH Password", value=ex_mgr_pw, type="password")
                
                if st.form_submit_button("Update Inventory (hosts.ini)"):
                    mgr_ip = current_config.get('wazuh_manager_ip')
                    if update_ini_inventory(mgr_ip, mgr_user, mgr_pass, agents_data):
                        st.success("Inventory updated!")

def render_prerequisites():
    st.title("Prerequisites Check")
    
    st.markdown("Run system checks using the `prerequisites` Ansible role.")

    # Options: Local or Inventory
    mode = st.radio("Target", ["Local Machine", "Inventory Hosts"])
    
    if st.button("Run Check"):
        st.info(f"Running checks on {mode}... Output will stream below.")
        
        playbook = ANSIBLE_DIR / "playbooks" / "prerequisites.yml"
        
        # Ensure we use our ansible.cfg
        env = os.environ.copy()
        env["ANSIBLE_CONFIG"] = str(ANSIBLE_DIR / "ansible.cfg")
        
        if mode == "Local Machine":
            # Run against localhost
            cmd = f"ansible-playbook {playbook} --connection=local -i localhost,"
        else:
            # Run against inventory
            if not HOSTS_INI_FILE.exists():
                st.error(f"Inventory file not found at {HOSTS_INI_FILE}. Please configure agents first.")
                return
            cmd = f"ansible-playbook {playbook} -i {HOSTS_INI_FILE}"

        st.code(cmd, language="bash")
        run_shell_stream(cmd, env=env)

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

def run_shell_stream(command, env=None):
    """Run command and stream output to Streamlit."""
    process = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        executable='/bin/zsh',
        env=env
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
