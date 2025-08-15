from providers.google_deeplink import build_google_flights_url
from providers.kiwi import search_kiwi
from providers.amadeus import search_amadeus_flights



OUTPUT_FILE = "data/live_deals.json"

def main():
    deals = []

    # Example: add a deal from Google Flights
    deals.append({
        "provider": "Google Flights",
        "url": build_google_flights_url("SYD", "LAX", "2025-09-10")
    })

    # Example: add Kiwi results
    kiwi_results = search_kiwi_flights("SYD", "LAX", "2025-09-10")
    deals.extend(kiwi_results)

    # Example: add Amadeus results
    amadeus_results = search_amadeus_flights("SYD", "LAX", "2025-09-10")
    deals.extend(amadeus_results)

    # Save to JSON
    with open(OUTPUT_FILE, "w") as f:
        json.dump(deals, f, indent=2)

if __name__ == "__main__":
    main()
