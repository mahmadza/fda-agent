import sqlite3
import argparse
import matplotlib.pyplot as plt
from src.config import Config


def get_latest_run_id(db_path: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT run_id, model_name FROM runs ORDER BY created_at DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    return row

def plot_latency(db_path: str = Config.DB_PATH, run_id=None):
    conn = sqlite3.connect(db_path)
    
    if not run_id:
        run_data = get_latest_run_id(db_path)
        if not run_data:
            print("No runs found.")
            return
        run_id, model_name = run_data
    else:
        cursor = conn.cursor()
        cursor.execute("SELECT model_name FROM runs WHERE run_id=?", (run_id,))
        model_name = cursor.fetchone()[0]

    # Get stats
    cursor = conn.cursor()
    cursor.execute("""
        SELECT section_name, duration_seconds 
        FROM section_stats 
        WHERE run_id = ? 
        ORDER BY id ASC
    """, (run_id,))
    data = cursor.fetchall()
    conn.close()

    if not data:
        print(f"No stats found for run {run_id}")
        return

    sections = [row[0] for row in data]
    times = [row[1] for row in data]

    # Plotting
    plt.figure(figsize=(10, 6))
    bars = plt.bar(sections, times, color='#4c72b0')
    
    plt.title(f'Latency by Section\nModel: {model_name} | Run: {run_id[:8]}...', fontsize=14)
    plt.ylabel('Seconds', fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    
    # Add labels
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                 f'{height:.0f}s',
                 ha='center', va='bottom')

    output_file = f"latency_{run_id[:8]}.png"
    plt.savefig(output_file)
    print(f"✅ Chart saved to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=Config.DB_PATH, help="Path to audit DB")
    parser.add_argument("--run-id", help="Optional Run ID")
    args = parser.parse_args()
    
    plot_latency(args.db, args.run_id)