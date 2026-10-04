import requests
import pandas as pd
from pathlib import Path

# Folder where fetched NAV data will be saved
RAW_FOLDER = Path("data/raw")
RAW_FOLDER.mkdir(parents=True, exist_ok=True)

# Schemes given in the task
SCHEMES = {
    "HDFC Top 100": 125497,
    "SBI Bluechip": 119551,
    "ICICI Bluechip": 120503,
    "Nippon Large Cap": 118632,
    "Axis Bluechip": 119092,
    "Kotak Bluechip": 120841,
}

BASE_URL = "https://api.mfapi.in/mf"

def fetch_nav(scheme_name, scheme_code):
    url = f"{BASE_URL}/{scheme_code}"

    print("\n" + "=" * 70)
    print(f"Fetching: {scheme_name}")
    print(f"Scheme Code: {scheme_code}")
    print(f"URL: {url}")

    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()

        data = response.json()

        # Convert NAV history into DataFrame
        df = pd.DataFrame(data.get("data", []))

        if df.empty:
            print("No NAV data found.")
            return

        # Add scheme information
        df["scheme_name"] = scheme_name
        df["amfi_code"] = scheme_code

        # Save raw CSV
        safe_name = scheme_name.lower().replace(" ", "_")
        output_file = RAW_FOLDER / f"{safe_name}_live_nav.csv"

        df.to_csv(output_file, index=False)

        print(f"NAV records fetched: {len(df)}")
        print(f"Saved to: {output_file}")
        print("\nFirst 5 records:")
        print(df.head())

    except requests.RequestException as e:
        print(f"API request failed: {e}")

    except ValueError as e:
        print(f"Invalid JSON response: {e}")

    except Exception as e:
        print(f"Unexpected error: {e}")


print("=" * 70)
print("MUTUAL FUND ANALYTICS - LIVE NAV FETCH")
print("=" * 70)

for scheme_name, scheme_code in SCHEMES.items():
    fetch_nav(scheme_name, scheme_code)

print("\n" + "=" * 70)
print("LIVE NAV FETCH COMPLETED")
print("=" * 70)