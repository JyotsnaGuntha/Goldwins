import pandas as pd
import os

files = ["BusBar_dimensions.xlsx", "MCCB Rating & Dimensions.xlsx"]

for f in files:
    if os.path.exists(f):
        print(f"\n--- {f} ---")
        try:
            df = pd.read_excel(f, header=None)
            print("First 10 rows:")
            print(df.head(10).to_string())
        except Exception as e:
            print(f"Error reading {f}: {e}")
    else:
        print(f"{f} not found")
