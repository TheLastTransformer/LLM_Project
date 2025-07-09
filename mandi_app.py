import sys
from fastapi import FastAPI
import requests
from fastapi.middleware.cors import CORSMiddleware

# Windows-specific fix for multiprocessing permission issues
if sys.platform == "win32":
    import multiprocessing
    multiprocessing.set_start_method('spawn', force=True)

app = FastAPI()

API_URL = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
API_KEY = "579b464db66ec23bdd000001cdd3946e44ce4aad7209ff7b23ac571b"

# Allow CORS for all origins (for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/mandi-prices")
def get_mandi_prices(state: str = "Haryana", district: str = "Gurgoan", commodity: str | None = None):
    params = {
        "api-key": API_KEY,
        "format": "json",
        "limit": 100,
        "filters[state.keyword]": state,
        "filters[district]": district,
    }
    if commodity and commodity.lower() != 'all':
        params["filters[commodity]"] = commodity
    response = requests.get(API_URL, params=params)
    if response.status_code == 200:
        return response.json()
    return {"error": "Failed to fetch data"}

@app.get("/mandi-filters")
def get_mandi_filters():
    params = {
        "api-key": API_KEY,
        "format": "json",
        "limit": 3000  # Fetch a larger number of records to build filter lists
    }
    try:
        response = requests.get(API_URL, params=params)
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()
        records = data.get("records", [])

        states = set()
        districts = {}
        commodities = set()

        for record in records:
            state = record.get("state")
            district = record.get("district")
            commodity = record.get("commodity")

            if state and state.lower() != 'state':  # Filter out invalid state entries
                states.add(state)
                if district:
                    if state not in districts:
                        districts[state] = set()
                    districts[state].add(district)
            if commodity:
                commodities.add(commodity)
        
        sorted_states = sorted(list(states))
        
        # Ensure all states have a corresponding district list (even if empty)
        for s in sorted_states:
            if s not in districts:
                districts[s] = set()

        sorted_districts = {s: sorted(list(d_set)) for s, d_set in districts.items()}
        sorted_commodities = sorted(list(commodities))

        return {
            "states": sorted_states,
            "districts": sorted_districts,
            "commodities": sorted_commodities,
        }
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to fetch filter data: {e}"}
