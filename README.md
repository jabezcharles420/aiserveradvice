# Server Monitoring & AI Advisor System

A comprehensive server monitoring solution that features a real-time dashboard, a backend receiver, a realistic server simulation engine, and an AI-powered expert advisor for diagnostics.

## 🚀 Features

- **Real-time Monitoring**: Track CPU, Memory, Disk, Temperature, Power Usage, Fan Speed, and Network metrics in real-time.
- **Server Simulation**: Realistic simulation of server behavior including load fluctuations, heating/cooling dynamics, and random failures/crashes.
- **Remote Control**: Send commands to servers to restart, hibernate, or adjust resource limits (Max CPU, Max Memory, Target Temp).
- **AI Expert Advisor**: Integrated DeepSeek-R1 AI model (via OpenRouter) to analyze historical data and provide actionable maintenance advice.
- **Diagnostic Reports**: Generate and download detailed text reports containing AI insights and raw historical data.

## 🛠️ Architecture

The system consists of four main components:

1.  **`dummy_receiver.py`**: A **FastAPI** backend that acts as the central hub. It receives metric updates from servers and serves data to the dashboard.
2.  **`server_simulation.py`**: Simulates multiple servers capable of receiving remote configuration updates. It posts metrics to the backend every 5 seconds.
3.  **`dashboard.py`**: A **Streamlit** frontend application that visualizes data and provides a control panel for user interaction.
4.  **`server_advisor.py`**: An AI module using **LangChain** and **OpenRouter** to analyze server history and generate expert advice.

## 📦 Prerequisites

- Python 3.8+
- An OpenRouter API Key (for specific AI features)

## ⚡ Installation

1.  **Clone the repository** (or navigate to the project directory):
    ```bash
    cd /path/to/project
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## 🚀 Usage Guide

To run the full system, you need to start three separate terminal processes.

### 1. Start the Backend Receiver
This component must run first to accept connections.
```bash
uvicorn dummy_receiver:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Start the Server Simulation
This will start 10+ simulated servers that begin reporting data.
```bash
python server_simulation.py
```

### 3. Start the Dashboard
Launch the user interface in your browser.
```bash
streamlit run dashboard.py
```

## 🧠 AI Advisor Setup

The AI Advisor uses the OpenRouter API.
1.  **Set the Environment Variable**:
    You need to set the `OPENROUTER_API_KEY` environment variable in your terminal before running the script.
    
    **Mac/Linux:**
    ```bash
    export OPENROUTER_API_KEY="your-api-key-here"
    ```

    **Windows (Command Prompt):**
    ```cmd
    set OPENROUTER_API_KEY=your-api-key-here
    ```

    **Windows (PowerShell):**
    ```powershell
    $env:OPENROUTER_API_KEY="your-api-key-here"
    ```

2.  (Optional) To generate a static history file for testing without waiting, run:
    ```bash
    python generate_history.py
    ```

## 📂 File Structure

- `dashboard.py`: Main UI application.
- `dummy_receiver.py`: Backend API server.
- `server_simulation.py`: Logic for simulated servers.
- `server_advisor.py`: AI analysis logic.
- `generate_history.py`: Utility to create sample CSV data.
- `server_history.csv`: Stored historical data for AI analysis.
- `requirements.txt`: Python dependencies.

## 📝 License
[MIT](https://choosealicense.com/licenses/mit/)
