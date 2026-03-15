# Slurm GPU Dashboard

A real-time, web-based GPU resource monitoring dashboard for [Slurm](https://slurm.schedmd.com/) HPC clusters. Built with [Streamlit](https://streamlit.io/), it connects to your cluster over SSH and provides rich, interactive visualizations of GPU allocation, job timelines, and node occupancy.

## Features

- **SSH-Based Authentication** — Securely connects to any Slurm cluster via SSH credentials. Supports a "Remember Me" option using encrypted browser cookies for automatic login.
- **Real-Time Job Data** — Fetches live `squeue` output from the cluster on demand, parsing running jobs with GPU, CPU, memory, and time information.
- **Resource Overview** — Stacked bar chart showing per-user GPU allocation broken down by node.
- **Node Occupancy View** — Visual rack-style layout displaying each GPU slot on every node, color-coded by job, with user, job ID, and elapsed time at a glance.
- **Job Timelines** — Interactive Gantt chart of all running jobs, showing start time, estimated end time, and GPU count.
- **Longest Running Jobs** — Horizontal bar chart ranking the top 20 longest-running jobs by elapsed hours.
- **Resource Density Analysis** — Bubble chart correlating elapsed time, GPU count, and CPU allocation per job.
- **Color Reshuffling** — Deterministic, hash-based color assignment for users and jobs, with a one-click reshuffle button for a fresh palette.
- **Responsive UI** — Custom CSS with Google Sans Flex font, optimized for a fixed 1280px content width with horizontal scroll support. Supports both light and dark Streamlit themes.

## Prerequisites

- **Python 3.8+**
- **Network access** to a Slurm cluster head node (or login node) via SSH
- A valid **SSH account** on the target cluster with permission to run `squeue`

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/jinkyusung/slurm-dashboard.git
   cd slurm-dashboard
   ```

2. **Create and activate a virtual environment (recommended):**

   ```bash
   python -m venv venv
   source venv/bin/activate   # Linux / macOS
   # venv\Scripts\activate    # Windows
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

## Dependencies

| Package | Purpose |
|---|---|
| [streamlit](https://pypi.org/project/streamlit/) | Web application framework |
| [pandas](https://pypi.org/project/pandas/) | Data manipulation and analysis |
| [paramiko](https://pypi.org/project/paramiko/) | SSH client for cluster communication |
| [plotly](https://pypi.org/project/plotly/) | Interactive chart rendering |
| [streamlit-cookies-manager](https://pypi.org/project/streamlit-cookies-manager/) | Encrypted cookie management for persistent login |
| [pytz](https://pypi.org/project/pytz/) | Timezone handling |

## Usage

### Starting the Dashboard

```bash
streamlit run app.py
```

By default, the app will be available at `http://localhost:8501`.

### Logging In

1. Enter the **Server IP / Host** and **Port** of your Slurm cluster's login node.
2. Provide your **SSH username** and **password**.
3. Optionally check **"Remember me"** to persist your credentials in an encrypted cookie for automatic login on future visits.
4. Click **"Connect to Cluster"**.

### Fetching Data

After logging in, click the **"Fetch Live Data"** button in the sidebar to pull the latest `squeue` data from the cluster. The dashboard will render all visualizations based on this data.

### Navigation

The sidebar provides quick-jump links to each dashboard section:

- **Resource Overview** — Per-user GPU allocation by node
- **Node Occupancy** — Physical GPU slot visualization
- **Job Timelines** — Gantt chart of running jobs
- **Run Time Ranking** — Top 20 longest-running jobs
- **Density Analysis** — Resource density bubble chart

### Additional Controls

- **Reshuffle Dashboard Colors** — Randomizes the color mapping for a fresh visual appearance.
- **Logout** — Clears stored credentials and returns to the login screen.

## Configuration

### Node Hardware Registry

The dashboard includes a built-in hardware configuration registry (`NODE_CONFIG` in `app.py`) that defines the GPU type, slot count, memory, and CPU count for each node. Update this dictionary to match your cluster's hardware:

```python
NODE_CONFIG = {
    "node01": {"gpu": "A100 (41GB)", "slots": 8, "mem": "512GB", "cpu": 96},
    "node02": {"gpu": "RTX 6000 (49GB)", "slots": 10, "mem": "512GB", "cpu": 80},
    # Add or modify entries as needed
}
```

### Cookie Encryption Password

The cookie encryption password defaults to a built-in value but can be overridden via the `COOKIES_PASSWORD` environment variable for production deployments:

```bash
export COOKIES_PASSWORD="your-secure-random-key"
streamlit run app.py
```

### Timezone

The dashboard defaults to **Asia/Seoul (KST)**. To change it, modify the `KST` variable at the top of `app.py`:

```python
KST = pytz.timezone('US/Eastern')  # Example: switch to US Eastern
```

> **Note:** The variable is named `KST` for historical reasons. When changing the timezone, you may also rename it (e.g., `LOCAL_TZ`) for clarity — just update all references in the file accordingly.

## Architecture

```
slurm-dashboard/
├── app.py              # Main Streamlit application (single-file)
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

The application follows a single-file architecture:

1. **Authentication Layer** — Validates SSH credentials against the target host via Paramiko. Credentials are optionally persisted using encrypted cookies.
2. **Data Acquisition** — Executes `squeue -h -t R -o "%i|%j|%t|%u|%P|%N|%C|%b|%m|%M|%l"` over SSH to fetch running job data with extended fields (job ID, name, state, user, partition, node list, CPUs, TRES, memory, elapsed time, time limit).
3. **Data Processing** — Parses the pipe-delimited output into a Pandas DataFrame, computing derived columns such as elapsed hours, start time, and estimated end time.
4. **Visualization** — Renders interactive Plotly charts (bar, timeline, scatter) and custom HTML/CSS for the node rack view.

## License

This project is provided as-is. See the repository for any applicable license information.
