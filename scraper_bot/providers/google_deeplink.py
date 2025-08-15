from urllib.parse import quote

CABIN_MAP = {
    "economy": "e",
    "premium": "p",
    "business": "c",
    "first": "f"
}

def build_google_flights_url(origin, dest, depart_date, return_date=None, cabin="economy", passengers=1, nonstop=True):
    c = CABIN_MAP.get((cabin or "economy").lower(), "e")
    
    if return_date:
        path = f"{origin}.{dest}.{depart_date}*{dest}.{origin}.{return_date}"
    else:
        path = f"{origin}.{dest}.{depart_date}"
    
    url = f"https://www.google.com/flights?hl=en#flt={quote(path)};c:{c};px:{passengers}"
    
    if nonstop:
        url += ";s:0"  # prefer nonstop flights
    
    return url

