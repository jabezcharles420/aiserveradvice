import os
import pandas as pd
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

# Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
CSV_FILE = "server_history.csv"
MODEL_NAME = "deepseek/deepseek-r1-0528:free"

def analyze_server_data(server_id, df):
    if not OPENROUTER_API_KEY:
        return "⚠️ OpenRouter API Key not found. Please set the OPENROUTER_API_KEY environment variable."

    # Filter data
    server_df = df[df['server_id'] == server_id]
    
    if server_df.empty:
        return f"No data found for Server {server_id}"

    # Prepare context: Concisely aggregated
    metrics = ['cpu', 'memory', 'temperature', 'fan_rpm', 'power_watts', 'net_down_speed', 'latency']
    
    summary_lines = []
    for metric in metrics:
        if metric in server_df.columns:
            avg_val = server_df[metric].mean()
            max_val = server_df[metric].max()
            summary_lines.append(f"- {metric.upper()}: Avg={avg_val:.1f}, Max={max_val:.1f}")
            
    stats_summary = "\n".join(summary_lines)
    
    # Only send last 5 entries to save context window
    recent_history = server_df.tail(5)[metrics + ['status', 'timestamp']].to_string(index=False)
    
    dates = f"From {server_df['timestamp'].min()} to {server_df['timestamp'].max()}"
    
    # Initialize LangChain
    chat = ChatOpenAI(
        api_key=OPENROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1",
        model=MODEL_NAME,
        temperature=0.7,
        max_tokens=2000 
    )  

    template = """
    You are an Expert Server Hardware Advisor. 
    Your goal is to analyze specific server metric aggregations and provide maintenance advice.
    
    Overview:
    - Server ID: {server_id}
    - Time Range: {dates}
    
    Aggregated Metrics (Average & Max):
    {stats}
    
    Last 5 Snapshots (Most Recent):
    {recent_history}
    
    Instructions:
    1. Look at the Avg vs Max values to identify instability.
    2. Check if Temperature is high relative to Fan Speed.
    3. Provide 3 bullet points of actionable advice suitable for a sysadmin.
    4. KEEP IT SHORT.
    """

    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | chat
    
    print("Generating insights (Aggregated)...")
    try:
        response = chain.invoke({
            "server_id": server_id,
            "dates": dates,
            "stats": stats_summary,
            "recent_history": recent_history
        })
        
        print(f"DEBUG: Raw Response Content: '{response.content}'") 
        if not response.content:
            return "Error: AI returned empty response. This might be due to the model reasoning taking up all tokens or a rate limit issue."
        return response.content
        
    except Exception as e:
        return f"Error generating advice: {e}\n(Model: {MODEL_NAME})"

def analyze_server(server_id):
    # CLI Wrapper
    print(f"Loading data for Server {server_id}...")
    try:
        df = pd.read_csv(CSV_FILE)
    except FileNotFoundError:
        print("CSV file not found.")
        return

    advice = analyze_server_data(server_id, df)
    
    print("\n" + "="*50)
    print(f"EXPERT ADVICE FOR SERVER {server_id}")
    print("="*50 + "\n")
    print(advice)

if __name__ == "__main__":
    analyze_server(1)
