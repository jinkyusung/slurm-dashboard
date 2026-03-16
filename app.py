import streamlit as st
import paramiko
import pandas as pd
import plotly.express as px
import io
import time
from datetime import datetime
from streamlit_cookies_manager import EncryptedCookieManager
import os
import pytz

# --- Timezone Setup ---
KST = pytz.timezone('Asia/Seoul')

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
    
    /* 3. Fully Responsive Full Width Layout */
    [data-testid="stMainBlockContainer"] {
        width: 100% !important;
        max-width: 100% !important;
        margin: 0 auto !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
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

    /* Sidebar Opaque Background Fix - Using solid hex colors to ensure 0% transparency */
    section[data-testid="stSidebar"] > div:first-child {
        background-color: #f0f2f6 !important; /* Standard Light Gray */
    }
    
    /* For Dark Mode users, we'll try to match the theme but keep it opaque */
    @media (prefers-color-scheme: dark) {
        section[data-testid="stSidebar"] > div:first-child {
            background-color: #1a1c24 !important; /* Dark Gray */
        }
    }

    [data-testid="stSidebar"] {
        background-color: #f0f2f6 !important;
        opacity: 1 !important;
    }

    /* Tight Sidebar Layout to Minimize Scrolling */
    [data-testid="stSidebarContent"] {
        padding: 0.0rem 0.8rem !important; /* Reduced top/side padding */
    }
    
    [data-testid="stSidebarContent"] .stMarkdown, 
    [data-testid="stSidebarContent"] .stHeader,
    [data-testid="stSidebarContent"] .stButton {
        margin-top: 0 !important;
        margin-bottom: 0.0rem !important; /* Very tight vertical gaps */
    }

    [data-testid="stSidebarContent"] h2, 
    [data-testid="stSidebarContent"] h3 {
        margin-bottom: 0.2rem !important; /* Even tighter for headers */
        padding-top: 0.2rem !important;
    }
    
    [data-testid="stSidebarContent"] hr {
        margin-top: 0 !important;
        margin-bottom: 0.4rem !important; /* Symmetric gap with elements */
        border: none;
        border-top: 1px solid rgba(128, 128, 128, 0.2);
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
if 'color_seed' not in st.session_state:
    st.session_state.color_seed = 0

# --- Connection Configuration handled dynamically ---

# --- Premium Color Palette (High contrast for white text) ---
# --- Premium Color Palette (With Dynamic Text Contrast) ---
APP_COLORS = [
    # Interleaved Light and Dark tones with unique hues
    {"bg": "#B71C1C", "fg": "#FFFFFF"}, {"bg": "#FFEB3B", "fg": "#000000"},
    {"bg": "#0D47A1", "fg": "#FFFFFF"}, {"bg": "#FFC107", "fg": "#000000"},
    {"bg": "#1B5E20", "fg": "#FFFFFF"}, {"bg": "#00BCD4", "fg": "#000000"},
    {"bg": "#4A148C", "fg": "#FFFFFF"}, {"bg": "#8BC34A", "fg": "#000000"},
    {"bg": "#E65100", "fg": "#FFFFFF"}, {"bg": "#CDDC39", "fg": "#000000"},
    {"bg": "#311B92", "fg": "#FFFFFF"}, {"bg": "#90CAF9", "fg": "#000000"},
    {"bg": "#C2185B", "fg": "#FFFFFF"}, {"bg": "#F48FB1", "fg": "#000000"},
    {"bg": "#3E2723", "fg": "#FFFFFF"}, {"bg": "#FF9800", "fg": "#000000"},
    {"bg": "#1A237E", "fg": "#FFFFFF"}, {"bg": "#BBDEFB", "fg": "#000000"},
    {"bg": "#004D40", "fg": "#FFFFFF"}, {"bg": "#DCE775", "fg": "#000000"},
    {"bg": "#880E4F", "fg": "#FFFFFF"}, {"bg": "#FFAB91", "fg": "#000000"},
    {"bg": "#2E7D32", "fg": "#FFFFFF"}, {"bg": "#B2DFDB", "fg": "#000000"},
    {"bg": "#1565C0", "fg": "#FFFFFF"}, {"bg": "#C8E6C9", "fg": "#000000"},
    {"bg": "#BF360C", "fg": "#FFFFFF"}, {"bg": "#E1BEE7", "fg": "#000000"},
    {"bg": "#33691E", "fg": "#FFFFFF"}, {"bg": "#FFE082", "fg": "#000000"},
    {"bg": "#006064", "fg": "#FFFFFF"}, {"bg": "#81D4FA", "fg": "#000000"},
    {"bg": "#4E342E", "fg": "#FFFFFF"}, {"bg": "#A5D6A7", "fg": "#000000"},
    {"bg": "#263238", "fg": "#FFFFFF"}, {"bg": "#B39DDB", "fg": "#000000"},
    {"bg": "#AD1457", "fg": "#FFFFFF"}, {"bg": "#F06292", "fg": "#000000"},
    {"bg": "#0277BD", "fg": "#FFFFFF"}, {"bg": "#BA68C8", "fg": "#000000"},
    {"bg": "#1976D2", "fg": "#FFFFFF"}, {"bg": "#4DB6AC", "fg": "#000000"}
]

import hashlib

def get_stable_color(identifier):
    """Returns a consistent color dict for a given string/ID using MD5 for collision resistance."""
    # Salt the identifier with the seed to completely change mapping on reshuffle
    salt = f"v1_{st.session_state.color_seed}_"
    hash_input = (salt + str(identifier)).encode()
    hash_hex = hashlib.md5(hash_input).hexdigest()
    hash_val = int(hash_hex, 16)
    return APP_COLORS[hash_val % len(APP_COLORS)]

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
            st.session_state.last_update = datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S')
            st.sidebar.success("Data Fetched Successfully")

if st.sidebar.button("Reshuffle Dashboard Colors", use_container_width=True):
    st.session_state.color_seed += 1
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.header("Quick Navigation")
st.sidebar.markdown("""
- [Resource Overview](#resource-overview)
- [Node Occupancy](#node-occupancy)
- [Job Timelines](#job-timelines)
- [Run Time Ranking](#ranking)
- [Density Analysis](#density)
""")

st.sidebar.markdown("---<br>") # Divider between Nav and Logout

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
    st.info(f"Last Synchronization Time (KST): {st.session_state.last_update}")
    
    if not st.session_state.squeue_raw_data.strip():
        st.warning("No active jobs currently running in the cluster.")
    else:
        try:
            # 1. Pipeline: Dataframe Processing
            columns = ['JOBID', 'NAME', 'ST', 'USER', 'PARTITION', 'NODELIST', 'CPUS', 'TRES_PER_NODE', 'MIN_MEMO', 'TIME', 'TIME_LIMIT']
            df = pd.read_csv(io.StringIO(st.session_state.squeue_raw_data), sep='|', names=columns)
            
            # Global reference time (KST)
            current_time = pd.Timestamp(datetime.now(KST)).replace(tzinfo=None).floor('S')
            
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

            # Create deterministic color map for Plotly to ensure persistence
            unique_users = df['USER'].unique()
            node_ids = list(NODE_CONFIG.keys())
            user_color_map = {u: get_stable_color(u)["bg"] for u in unique_users}
            node_color_map = {n: get_stable_color(n)["bg"] for n in node_ids}

            fig_bar = px.bar(
                user_node_df, x='USER', y='GPU_Count', color='NODELIST',
                labels={'GPU_Count': '<b>GPU Count</b>', 'USER': '<b>User Name</b>'},
                category_orders={'USER': user_total_order},
                text='GPU_Count',
                color_discrete_map=node_color_map
            )
            fig_bar.update_layout(barmode='stack', height=350, margin=dict(t=30, b=20),
                                    font=dict(size=14, family="Google Sans Flex"))
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
                    flex-wrap: wrap;
                    align-items: center; /* Vertically center node info with slots */
                    gap: 10px 15px;
                    background-color: transparent;
                    padding: 8px 0;
                    border-bottom: 1px solid rgba(128, 128, 128, 0.2);
                }
                .node-info {
                    width: 120px;
                    flex-shrink: 0;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    gap: 1px; /* Tight spacing between lines */
                }
                .node-info b { line-height: 1.2; }
                .node-info span { line-height: 1.1; }
                .slots-wrapper {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 6px;
                    flex-grow: 1;
                    min-width: 300px; /* Ensure it has enough room to be useful */
                }
                .gpu-slot {
                    width: 78px;
                    height: 62px;
                    flex-shrink: 0;
                    border-radius: 4px;
                    text-align: center;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    padding: 1px;
                    border: 1px solid rgba(0,0,0,0.1);
                }
                .gpu-slot-empty {
                    width: 78px;
                    height: 62px;
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
                        color_data = get_stable_color(jobid)
                        bg_color = color_data["bg"]
                        text_color = color_data["fg"]
                        # Build compact slot HTML with dynamic text color
                        slots_html += f'<div class="gpu-slot" style="background-color: {bg_color}; color: {text_color};"><div style="font-size:11px; font-weight:700; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">{user}</div><div style="font-size:10px; opacity:0.85; margin: 1px 0;">#{jobid}</div><div style="font-size:11px; background:rgba(255,255,255,0.2); border-radius:2px; font-weight:600;">{runtime}</div></div>'
                    else:
                        slots_html += '<div class="gpu-slot-empty"></div>'

                # Render the entire node row using flex-based info box for better alignment
                node_html = f"""<div class="node-row"><div class="node-info"><b style="font-size:19px; color:var(--text-color);">{node_id.upper()}</b><span style="font-size:13px; color:var(--text-color); opacity:0.8; font-weight:500;">{config['gpu']}</span><span style="font-size:12px; color:var(--text-color); opacity:0.6;">RAM {config['mem']} / {config['cpu']}C</span></div><div class="slots-wrapper">{slots_html}</div></div>"""
                st.markdown(node_html, unsafe_allow_html=True)

            st.markdown('<div style="margin-top: 50px;"></div>', unsafe_allow_html=True)
            st.markdown("---")

            # SECTION 3: JOB TIMELINES
            st.header("Individual Job Timelines", anchor="job-timelines")
            df_gantt_sorted = df.sort_values(by='Start_Time', ascending=True)
            fig_user_gantt = px.timeline(
                df_gantt_sorted, x_start="Start_Time", x_end="Estimated_End_Time", 
                y="Unique_Job_Label", color="USER", hover_name="NAME",
                text="GPU_Count",
                hover_data={"JOBID":True, "Elapsed_Hours":":.2f", "USER":True},
                color_discrete_map=user_color_map
            )
            gantt_height = max(400, len(df) * 30)
            fig_user_gantt.update_layout(height=gantt_height, showlegend=True, 
                                        xaxis=dict(tickformat="%m/%d %H:%M"),
                                        yaxis_title="Job [User & ID]",
                                        font=dict(size=14, family="Google Sans Flex"))
            fig_user_gantt.update_yaxes(autorange="reversed")
            st.plotly_chart(fig_user_gantt, use_container_width=True)

            st.markdown("---")

            # SECTION 4: LONG-RUNNING RANKING
            st.header("Time Spending (TOP 20)", anchor="ranking")
            top_20_df = df.sort_values(by='Elapsed_Hours', ascending=False).head(20)
            fig_rank = px.bar(
                top_20_df, x='Elapsed_Hours', y='Unique_Job_Label', color='USER',
                orientation='h', text='Elapsed_Hours',
                labels={'Elapsed_Hours': 'Run Time (Hours)', 'Unique_Job_Label': 'Job'},
                color_discrete_map=user_color_map
            )
            fig_rank.update_traces(texttemplate='%{text:.1f}h', textposition='outside')
            fig_rank.update_layout(height=600, yaxis={'categoryorder':'total ascending'},
                                    font=dict(size=14, family="Google Sans Flex"))
            st.plotly_chart(fig_rank, use_container_width=True)

            st.markdown("---")

            # SECTION 5: RESOURCE DENSITY ANALYSIS
            st.header("Resource Density Analysis", anchor="density")
            fig_bubble = px.scatter(
                df, x="Elapsed_Hours", y="GPU_Count", size="CPUS", color="USER",
                hover_name="Unique_Job_Label", size_max=60,
                labels={'Elapsed_Hours': 'Elapsed Hours', 'GPU_Count': 'Allocated GPUs', 'CPUS': 'CPU Allocation'},
                color_discrete_map=user_color_map
            )
            fig_bubble.update_layout(height=500, font=dict(size=14, family="Google Sans Flex"))
            st.plotly_chart(fig_bubble, use_container_width=True)
                
        except Exception as e:
            st.error(f"Data Processing Error:\n{e}")
            with st.expander("Show Raw Data Trace"):
                st.code(st.session_state.squeue_raw_data)

else:
    st.info("Please click the 'Fetch Live Data' button on the sidebar to initialize the dashboard.")