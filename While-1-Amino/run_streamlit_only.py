#!/usr/bin/env python3
import subprocess
import webbrowser
import time
import threading
import os
import sys

def open_browser():
    """Open the browser after a delay"""
    # Wait for Streamlit to start
    time.sleep(3)
    # Open browser
    webbrowser.open('http://localhost:8501')
    print("✅ Opened AminoVerse in your web browser.")

def run_streamlit():
    """Run the Streamlit app"""
    print("🧬 Starting AminoVerse - ChatGPT for Proteins...")
    print("📊 Frontend will be available at: http://localhost:8501")
    
    # Start browser in a separate thread
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # Run Streamlit
    subprocess.run(["streamlit", "run", "streamlit_app.py"], 
                   cwd=os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    run_streamlit()
