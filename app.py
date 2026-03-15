import streamlit as st
import paramiko
import pandas as pd
import plotly.express as px
import io
import time
from datetime import datetime
from streamlit_cookies_manager import EncryptedCookieManager
import os

# --- Page Configuration ---
st.set_page_config(page_title="Slurm GPU Dash", layout="wide")

# --- Cookie Management (for Automatic Login) ---
# Note: In a production environment, use environment variables for passwords.
cookies = EncryptedCookieManager(
    password=os.environ.get("COOKIES_PASSWORD", "viplab_secret_cookie_key_9988"),
)
if not cookies.ready():
    st.stop()


# --- Premium UI/UX Custom CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Google+Sans+Flex:opsz,wght@6..144,1..1000&display=swap');

    /* 1. Explicitly target MAIN content only, avoiding sidebar & icons */
    [data-testid="stMainBlockContainer"] h1, 
    [data-testid="stMainBlockContainer"] h2, 
    [data-testid="stMainBlockContainer"] h3,
    [data-testid="stMainBlockContainer"] p,
    [data-testid="stMainBlockContainer"] li,
    [data-testid="stMainBlockContainer"] .stMetric div,
    .login-box * {
        font-family: 'Google Sans Flex', sans-serif !important;
    }

    /* 2. Global Metric Label Tuning */
    [data-testid="stMetricLabel"] {
        font-family: 'Google Sans Flex', sans-serif !important;
    }
    
    /* 3. Fixed width for 2/3 of 16:9 screen (1280px) and Horizontal Scroll */
    [data-testid="stAppViewContainer"] {
        overflow-x: auto !important;
    }
    
    [data-testid="stMainBlockContainer"] {
        min-width: 1280px !important;
        max-width: 1280px !important;
        margin: 0 auto !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }

    .stApp {
        font-size: 1.05rem;
    }

    /* Headings Styling (Main only) */
    h1 { font-size: 2.22rem !important; font-weight: 700 !important; color: var(--text-color); }
    h2 { font-size: 1.8rem !important; font-weight: 700 !important; color: var(--text-color); opacity: 0.9; margin-top: 2rem !important; }
    h3 { font-size: 1.3rem !important; font-weight: 600 !important; color: var(--text-color); opacity: 0.8; }

    /* Login Page Aesthetics */
    .login-container {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 80vh;
    }
    .login-box {
        background: var(--background-color);
        padding: 3rem;
        border-radius: 16px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        width: 450px;
        text-align: center;
        border: 1px solid rgba(128, 128, 128, 0.2);
    }

    /* Divider Styling */
    hr { margin: 2rem 0 !important; border-top: 1px solid rgba(128, 128, 128, 0.2) !important; }

    /* Sidebar Background (Support Light/Dark) */
    section[data-testid="stSidebar"] {
        background-color: rgba(128, 128, 128, 0.05); /* Very subtle tint */
    }
    </style>
    """, unsafe_allow_html=True)

def validate_ssh_credentials(host, port, username, password):
    """Attempts to connect to the SSH server to validate credentials."""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, port=port, username=username, password=password, timeout=5)
        ssh.close()
        return True
    except:
        return False

# --- Authentication Logic ---
def check_auth():
    if st.session_state.get("authenticated") == True:
        return True
    
    # Check cookies for persisted login
    if cookies.get("authenticated") == "true":
        # Restore credentials from cookies to session state
        st.session_state.host = cookies.get("ssh_host")
        st.session_state.port = int(cookies.get("ssh_port") or 22)
        st.session_state.username = cookies.get("ssh_username")
        st.session_state.password = cookies.get("ssh_password")
        st.session_state.authenticated = True
        return True
        
    return False

if not check_auth():
    # Use columns to center the login box
    _, col, _ = st.columns([1, 2, 1])
    with col:
        with st.container():
            st.title("Cluster Access")
            st.markdown("Please enter your server credentials to access the Dashboard")
            
            c1, c2 = st.columns([3, 1])
            with c1: login_host = st.text_input("Server IP / Host")
            with c2: login_port = st.text_input("Port")
            
            login_user = st.text_input("Server Username")
            login_pass = st.text_input("Server Password", type="password")
            remember_me = st.checkbox("Remember me (Automatic Login)")
            
            if st.button("Connect to Cluster", use_container_width=True):
                with st.spinner("Verifying credentials..."):
                    try:
                        port_int = int(login_port)
                        if validate_ssh_credentials(login_host, port_int, login_user, login_pass):
                            st.session_state.authenticated = True
                            st.session_state.host = login_host
                            st.session_state.port = port_int
                            st.session_state.username = login_user
                            st.session_state.password = login_pass
                            
                            cookies["authenticated"] = "true"
                            cookies["ssh_host"] = login_host
                            cookies["ssh_port"] = str(port_int)
                            cookies["ssh_username"] = login_user
                            cookies["ssh_password"] = login_pass # Encrypted by EncryptedCookieManager
                            
                            if remember_me:
                                cookies.save() 
                            
                            st.success("Connected! Redirecting...")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Invalid server credentials or connection timeout.")
                    except ValueError:
                        st.error("Port must be a valid integer.")
    st.stop()

# Short-hand references for the rest of the app
HOST = st.session_state.host
PORT = st.session_state.port
USERNAME = st.session_state.username
PASSWORD = st.session_state.password



# --- Main App Starts Here (Only if Authenticated) ---
st.title("Real-time Slurm GPU Dashboard")
st.markdown("Connects to the Slurm cluster and visualizes resource allocation in real-time.")

# --- Session State Initialization ---
if 'squeue_raw_data' not in st.session_state:
    st.session_state.squeue_raw_data = None
if 'last_update' not in st.session_state:
    st.session_state.last_update = None

# --- Connection Configuration handled dynamically ---

# --- Premium Color Palette (High contrast for white text) ---
APP_COLORS = [
    "#D32F2F", "#1976D2", "#388E3C", "#F57C00", "#7B1FA2", 
    "#0097A7", "#5D4037", "#455A64", "#C2185B", "#512DA8", 
    "#303F9F", "#0288D1", "#00796B", "#689F38", "#827717", 
    "#E64A19", "#FF8F00", "#2E7D32", "#1565C0", "#AD1457",
    "#6A1B9A", "#283593", "#0277BD", "#00838F", "#00695C",
    "#558B2F", "#9E9D24", "#263238", "#EF6C00", "#BF360C"
]

# --- Hardware Specification Registry ---
NODE_CONFIG = {
    "node01": {"gpu": "A100 (41GB)", "slots": 8, "mem": "512GB", "cpu": 96},
    "node02": {"gpu": "RTX 6000 (49GB)", "slots": 10, "mem": "512GB", "cpu": 80},
    "node03": {"gpu": "RTX 6000 (49GB)", "slots": 10, "mem": "512GB", "cpu": 80},
    "node04": {"gpu": "RTX A5000 (25GB)", "slots": 8, "mem": "256GB", "cpu": 80},
    "node05": {"gpu": "RTX A4000 (16GB)", "slots": 10, "mem": "256GB", "cpu": 80},
    "node06": {"gpu": "RTX A6000 (49GB)", "slots": 8, "mem": "256GB", "cpu": 96},
    "node07": {"gpu": "RTX A6000 (49GB)", "slots": 8, "mem": "512GB", "cpu": 96},
}

# --- Backend: SSH Communication ---
def get_squeue_via_ssh(host, port, username, password):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, port=port, username=username, password=password, timeout=10)

        # Command with extended fields for time limit and resource info
        command = 'squeue -h -t R -o "%i|%j|%t|%u|%P|%N|%C|%b|%m|%M|%l"'
        stdin, stdout, stderr = ssh.exec_command(command)
        
        output = stdout.read().decode('utf-8').strip()
        error = stderr.read().decode('utf-8').strip()
        ssh.close()

        if error and not output:
            st.error(f"Squeue Command Error:\n{error}")
            return None
        return output
    except Exception as e:
        st.error(f"SSH Connection Failed: {e}")
        return None

# --- Logic: Time Parsing ---
def parse_time_string(time_str):
    """Converts Slurm time format ([DD-]HH:MM:SS) to pd.Timedelta"""
    try:
        s = str(time_str).strip()
        if not s or s in ['INVALID', 'UNLIMITED', 'NONE']:
            return pd.Timedelta(days=7) # Default limit for visualization
        
        if '-' in s:
            s = s.replace('-', ' days ')
        
        parts = s.split(':')
        if len(parts) == 2 and 'days' not in s: 
            s = f"00:{s}"
            
        td = pd.to_timedelta(s, errors='coerce')
        return td if pd.notnull(td) else pd.Timedelta(seconds=0)
    except:
        return pd.Timedelta(seconds=0)

def parse_gpu_count(tres_str):
    """Extracts GPU numbers from Slurm TRES string"""
    tres_str = str(tres_str).strip()
    if pd.isna(tres_str) or 'gres/gpu:' not in tres_str:
        return 0
    try:
        return int(tres_str.split('gres/gpu:')[1].split(',')[0])
    except:
        return 0

# --- Sidebar: Integration Control ---
st.sidebar.header("Control Panel")
st.sidebar.info(f"Target Host: {HOST}\n\nUser: {USERNAME}")

if st.sidebar.button("Fetch Live Data", use_container_width=True):
    with st.spinner("Connecting to cluster and fetching squeue data..."):
        raw_data = get_squeue_via_ssh(HOST, PORT, USERNAME, PASSWORD)
        if raw_data is not None:
            st.session_state.squeue_raw_data = raw_data
            st.session_state.last_update = time.strftime('%Y-%m-%d %H:%M:%S')
            st.sidebar.success("Data Fetched Successfully")

st.sidebar.markdown("---")
st.sidebar.header("Quick Navigation")
st.sidebar.markdown("""
- [Resource Overview](#resource-overview)
- [Node Occupancy](#node-occupancy)
- [Job Timelines](#job-timelines)
- [Run Time Ranking](#ranking)
- [Density Analysis](#density)
""")

if st.sidebar.button("Logout", type="primary", use_container_width=True):
    cookies["authenticated"] = "false"
    cookies["ssh_host"] = ""
    cookies["ssh_port"] = ""
    cookies["ssh_username"] = ""
    cookies["ssh_password"] = ""
    cookies.save()
    st.session_state.authenticated = False
    st.session_state.host = None
    st.session_state.port = None
    st.session_state.username = None
    st.session_state.password = None
    st.rerun()

# --- Main Dashboard Rendering ---
if st.session_state.squeue_raw_data:
    st.info(f"Last Synchronization Time: {st.session_state.last_update}")
    
    if not st.session_state.squeue_raw_data.strip():
        st.warning("No active jobs currently running in the cluster.")
    else:
        try:
            # 1. Pipeline: Dataframe Processing
            columns = ['JOBID', 'NAME', 'ST', 'USER', 'PARTITION', 'NODELIST', 'CPUS', 'TRES_PER_NODE', 'MIN_MEMO', 'TIME', 'TIME_LIMIT']
            df = pd.read_csv(io.StringIO(st.session_state.squeue_raw_data), sep='|', names=columns)
            
            # Global reference time
            current_time = pd.Timestamp.now().floor('S')
            
            # Time Vectorization
            df['Elapsed_Time'] = df['TIME'].apply(parse_time_string)
            df['Limit_Time'] = df['TIME_LIMIT'].apply(parse_time_string)
            df['Start_Time'] = current_time - df['Elapsed_Time']
            df['Estimated_End_Time'] = df['Start_Time'] + df['Limit_Time']
            df['Elapsed_Hours'] = df['Elapsed_Time'].dt.total_seconds() / 3600
            
            # Cleaning and Pre-processing
            df = df.dropna(subset=['Start_Time', 'Estimated_End_Time'])
            df['GPU_Count'] = df['TRES_PER_NODE'].apply(parse_gpu_count).astype(int)
            # Use Unique_Job_Label carefully
            df['Unique_Job_Label'] = df['USER'] + " [" + df['JOBID'].astype(str) + "]"
            
            # --- Analytics: Key Performance Indicators ---
            col1, col2, col3, col4 = st.columns(4)
            total_gpus = df['GPU_Count'].sum()
            active_users = df['USER'].nunique()
            active_nodes = df['NODELIST'].nunique()
            total_jobs = len(df)
            
            with col1: st.metric("Allocated GPUs", f"{total_gpus}")
            with col2: st.metric("Active Users", f"{active_users}")
            with col3: st.metric("Active Nodes", f"{active_nodes}")
            with col4: st.metric("Running Jobs", f"{total_jobs}")

            st.markdown("---")

            # SECTION 1: RESOURCE OVERVIEW
            st.header("Resource Overview", anchor="resource-overview")
            user_node_df = df.groupby(['USER', 'NODELIST'])['GPU_Count'].sum().reset_index()
            user_node_df = user_node_df[user_node_df['GPU_Count'] > 0]
            user_total_order = user_node_df.groupby('USER')['GPU_Count'].sum().sort_values(ascending=False).index.tolist()
            
            fig_bar = px.bar(
                user_node_df, x='USER', y='GPU_Count', color='NODELIST',
                labels={'GPU_Count': '<b>GPU Count</b>', 'USER': '<b>User Name</b>'},
                category_orders={'USER': user_total_order},
                text='GPU_Count',
                color_discrete_sequence=APP_COLORS
            )
            fig_bar.update_layout(barmode='stack', height=400, margin=dict(t=30, b=20),
                                    font=dict(size=14, family="Google Sans Flex"))
            fig_bar.update_traces(textfont_color='white', textposition='inside')
            st.plotly_chart(fig_bar, use_container_width=True)
            
            st.markdown("---")
            
            # SECTION 2: PHYSICAL NODE MONITORING
            st.header("Detailed Node Occupancy", anchor="node-occupancy")
            
            # Internal CSS for Rack View elements within the 1280px container
            st.markdown("""
                <style>
                .node-row, .node-info, .slots-wrapper, .gpu-slot, .gpu-slot div {
                    font-family: 'Google Sans Flex', sans-serif !important;
                }
                .node-row {
                    display: flex;
                    align-items: center;
                    background-color: transparent;
                    padding: 10px 0;
                    border-bottom: 1px solid rgba(128, 128, 128, 0.2);
                }
                .node-info {
                    width: 120px;
                    flex-shrink: 0;
                    margin-right: 15px;
                }
                .slots-wrapper {
                    display: flex;
                    gap: 10px;
                    flex-grow: 1;
                }
                .gpu-slot {
                    width: 95px;
                    height: 72px;
                    flex-shrink: 0;
                    border-radius: 4px;
                    text-align: center;
                    color: white; /* Keep white text for colored background */
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    padding: 2px;
                    border: 1px solid rgba(0,0,0,0.1);
                }
                .gpu-slot-empty {
                    width: 95px;
                    height: 72px;
                    flex-shrink: 0;
                    background-color: rgba(128, 128, 128, 0.05);
                    border: 1px dashed rgba(128, 128, 128, 0.3);
                    border-radius: 4px;
                }
                </style>
            """, unsafe_allow_html=True)

            for node_id, config in NODE_CONFIG.items():
                node_jobs = df[df['NODELIST'] == node_id].sort_values(by='Elapsed_Hours', ascending=False)
                total_slots = config['slots']
                
                # Assign to slots
                current_slots = []
                idx = 0
                for _, job in node_jobs.iterrows():
                    for _ in range(job['GPU_Count']):
                        if idx < total_slots:
                            current_slots.append((job['USER'], job['JOBID'], job['TIME']))
                            idx += 1
                while len(current_slots) < total_slots:
                    current_slots.append(None)
                
                slots_html = ""
                for slot in current_slots:
                    if slot:
                        user, jobid, runtime = slot
                        c_idx = hash(str(jobid)) % len(APP_COLORS)
                        # Build compact slot HTML without any leading spaces or newlines
                        slots_html += f'<div class="gpu-slot" style="background-color: {APP_COLORS[c_idx]};"><div style="font-size:11px; font-weight:700; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">{user}</div><div style="font-size:10px; opacity:0.85; margin: 1px 0;">#{jobid}</div><div style="font-size:11px; background:rgba(255,255,255,0.2); border-radius:2px; font-weight:600;">{runtime}</div></div>'
                    else:
                        slots_html += '<div class="gpu-slot-empty"></div>'

                # Render the entire node row using compact HTML to prevent markdown parsing errors
                node_html = f"""<div class="node-row"><div class="node-info"><b style="font-size:19px; color:var(--text-color);">{node_id.upper()}</b><br><span style="font-size:13px; color:var(--text-color); opacity:0.8; font-weight:500;">{config['gpu']}</span><br><span style="font-size:12px; color:var(--text-color); opacity:0.6;">RAM {config['mem']} / {config['cpu']}C</span></div><div class="slots-wrapper">{slots_html}</div></div>"""
                st.markdown(node_html, unsafe_allow_html=True)

            st.markdown("---")

            # SECTION 3: JOB TIMELINES
            st.header("Individual Job Timelines", anchor="job-timelines")
            df_gantt_sorted = df.sort_values(by='Start_Time', ascending=True)
            fig_user_gantt = px.timeline(
                df_gantt_sorted, x_start="Start_Time", x_end="Estimated_End_Time", 
                y="Unique_Job_Label", color="USER", hover_name="NAME",
                text="GPU_Count",
                hover_data={"JOBID":True, "Elapsed_Hours":":.2f", "USER":True},
                color_discrete_sequence=APP_COLORS
            )
            gantt_height = max(500, len(df) * 35)
            fig_user_gantt.update_layout(height=gantt_height, showlegend=True, 
                                        xaxis=dict(tickformat="%m/%d %H:%M"),
                                        yaxis_title="Job Identifier [User & ID]",
                                        font=dict(size=14, family="Google Sans Flex"))
            fig_user_gantt.update_yaxes(autorange="reversed")
            fig_user_gantt.update_traces(textfont_color='white', textposition='inside')
            st.plotly_chart(fig_user_gantt, use_container_width=True)

            st.markdown("---")

            # SECTION 4: LONG-RUNNING RANKING
            st.header("Top 20 Longest Running Jobs", anchor="ranking")
            top_20_df = df.sort_values(by='Elapsed_Hours', ascending=False).head(20)
            fig_rank = px.bar(
                top_20_df, x='Elapsed_Hours', y='Unique_Job_Label', color='USER',
                orientation='h', text='Elapsed_Hours',
                labels={'Elapsed_Hours': 'Run Time (Hours)', 'Unique_Job_Label': 'Job'},
                color_discrete_sequence=APP_COLORS
            )
            fig_rank.update_traces(texttemplate='%{text:.1f}h', textposition='inside', textfont_color='white')
            fig_rank.update_layout(height=700, yaxis={'categoryorder':'total ascending'},
                                    font=dict(size=14, family="Google Sans Flex"))
            st.plotly_chart(fig_rank, use_container_width=True)

            st.markdown("---")

            # SECTION 5: RESOURCE DENSITY ANALYSIS
            st.header("Resource Density Analysis", anchor="density")
            fig_bubble = px.scatter(
                df, x="Elapsed_Hours", y="GPU_Count", size="CPUS", color="USER",
                hover_name="Unique_Job_Label", size_max=60,
                labels={'Elapsed_Hours': 'Elapsed Hours', 'GPU_Count': 'Allocated GPUs', 'CPUS': 'CPU Allocation'},
                color_discrete_sequence=APP_COLORS
            )
            fig_bubble.update_layout(height=600, font=dict(size=14, family="Google Sans Flex"))
            st.plotly_chart(fig_bubble, use_container_width=True)
                
        except Exception as e:
            st.error(f"Data Processing Error:\n{e}")
            with st.expander("Show Raw Data Trace"):
                st.code(st.session_state.squeue_raw_data)

else:
    st.info("Please click the 'Fetch Live Data' button on the sidebar to initialize the dashboard.")