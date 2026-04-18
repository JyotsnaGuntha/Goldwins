import os
import webbrowser
import time

# Start streamlit
os.system("streamlit run app.py")

# Open browser after slight delay
time.sleep(3)
webbrowser.open("http://localhost:8501")