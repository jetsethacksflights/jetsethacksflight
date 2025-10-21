"""
Webhook Sender for JetSet Hacks Flight Data
Transforms scraped flight data and sends to Supabase webhook
"""

import json
import requests
from pathlib import Path
from datetime import datetime

# Supabase webhook configuration
WEBHOOK_URL = "https://lwuzpvwiviwvqjuzmxff.supabase.co/functions/v1/receive-scraped-flights"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imx3dXpwdndpdml3dnFqdXpteGZmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTYxOTc2OTcsImV4cCI6MjA3MTc3MzY5N30.JHlpooEeJnivIsr_b57l0Ae1vIqTD5wEADWCb9FvwZc"

# City name mappings for common airports
AIRPORT_CITIES = {
    "SYD": "Sydney", "MEL": "Melbourne", "BNE": "Brisbane", "PER": "Perth", "ADL": "Adelaide",
    "DPS": "Denpasar", "NRT": "Tokyo", "HND": "Tokyo", "LAX": "Los Angeles", "SFO": "San Francisco",
    "JFK": "New York", "LHR": "London", "CDG": "Paris", "DXB": "Dubai", "SIN": "Singapore",
    "HKG": "Hong Kong", "BKK": "Bangkok", "ICN": "Seoul", "AKL": "Auckland", "CHC": "Christchurch",
}

def get_city_name(airport_code):
    """Get city name from airport code"""
    return AIRPORT_CITIES.get(airport_code, airport_code)

def transform_flight_data(item):
    """
    Transform Amadeus scraper format to webhook format
    
    Amadeus format:
    {
        "airline": "QF",
        "flight_number": "QF123",
        "origin": "SYD",
        "destination": "DPS",
        "departure_time": "2025-01-15T10:30:00",
        "arrival_time": "2025-01-15T16:45:00",
        "duration": "PT6H15M",
        "price": 450.00,
        "currency": "AUD",
        "cabin_class": "ECONOMY",
        "stops": 0,
        "source": "amadeus",
        "scraped_at": "2025-01-15T08:00:00"
    }
    """
    
    # Skip if no price
    if not item.get("price"):
        return None
    
    # Extract basic info (Amadeus format)
    origin = item.get("origin", "").upper()
    destination = item.get("destination", "").upper()
    airline = item.get("airline", "Unknown")
    flight_num = item.get("flight_number", "")
    
    # Parse departure/arrival times (ISO format: "2025-01-15T10:30:00")
    departure_time = "08:00:00"
    arrival_time = "11:30:00"
    
    dep_timestamp = item.get("departure_time", "")
    arr_timestamp = item.get("arrival_time", "")
    
    if "T" in dep_timestamp:
        departure_time = dep_timestamp.split("T")[1].split("+")[0].split("Z")[0]
    
    if "T" in arr_timestamp:
        arrival_time = arr_timestamp.split("T")[1].split("+")[0].split("Z")[0]
    
    # Parse duration (Amadeus ISO 8601 format: "PT6H15M")
    duration = "3h 30m"
    if item.get("duration"):
        dur_str = item["duration"].replace("PT", "")
        if "H" in dur_str and "M" in dur_str:
            hours = dur_str.split("H")[0]
            minutes = dur_str.split("H")[1].replace("M", "")
            duration = f"{hours}h {minutes}m"
        elif "H" in dur_str:
            hours = dur_str.replace("H", "")
            duration = f"{hours}h 0m"
        elif "M" in dur_str:
            minutes = dur_str.replace("M", "")
            duration = f"0h {minutes}m"
    
    # Extract cabin class
    cabin = item.get("cabin_class", "economy").lower()
    
    # Stops
    stops = item.get("stops", 0)
    
    return {
        "airline": airline,
        "flight_number": flight_num,
        "origin_airport": origin,
        "origin_city": get_city_name(origin),
        "destination_airport": destination,
        "destination_city": get_city_name(destination),
        "departure_time": departure_time,
        "arrival_time": arrival_time,
        "duration": duration,
        "price": int(float(item.get("price", 0))),
        "currency": item.get("currency", "AUD"),
        "stops": stops,
        "cabin_class": cabin,
        "booking_url": "",  # Amadeus doesn't provide direct booking URLs
        "features": [],
        "rating": 4.0,
    }

def send_to_webhook():
    """
    Read scraped data from live_deals.json and send to Supabase webhook
    """
    # Read scraped data
    data_file = Path("data/live_deals.json")
    
    if not data_file.exists():
        print("❌ Error: data/live_deals.json not found. Run scrape.py first.")
        return False
    
    with open(data_file, 'r', encoding='utf-8') as f:
        scraped_data = json.load(f)
    
    items = scraped_data.get("items", [])
    
    if not items:
        print("⚠️  No items found in live_deals.json")
        return False
    
    print(f"📦 Found {len(items)} items in live_deals.json")
    
    # Transform data
    transformed_flights = []
    for item in items:
        flight = transform_flight_data(item)
        if flight:  # Only add if transformation succeeded
            transformed_flights.append(flight)
    
    if not transformed_flights:
        print("⚠️  No valid flights to send after transformation")
        return False
    
    print(f"✅ Transformed {len(transformed_flights)} flights")
    
    # Prepare webhook payload
    payload = {
        "flights": transformed_flights,
        "source": "github_bot_amadeus"
    }
    
    # Send to webhook
    try:
        headers = {
            "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
            "Content-Type": "application/json"
        }
        
        print(f"🚀 Sending {len(transformed_flights)} flights to webhook...")
        
        response = requests.post(
            WEBHOOK_URL,
            json=payload,
            headers=headers,
            timeout=30
        )
        
        response.raise_for_status()
        
        result = response.json()
        print(f"✅ Success! Webhook response: {result}")
        print(f"✅ Inserted {result.get('inserted', 0)} flights into database")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error sending to webhook: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("JetSet Hacks - Webhook Sender")
    print("=" * 50)
    send_to_webhook()
