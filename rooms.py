import requests
TELEGRAM_BOT_TOKEN = '7883099850:AAFGMRnEZGE5vKH6CUMHyZMmyBu3Sdl0pts'
API_URL_BASE = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/'

def all_rooms_list_grouped(queue_data):
    """Builds a grouped list of rooms. Rooms with single-character RoomID are grouped under 'General OPD'."""
    if not queue_data:
        return "No queue data available."

    all_rooms = [
        "ROOM 8", "ROOM 5", "ROOM 7", "ROOM 6", "ROOM 301",
        "ROOM PSY 1", "ROOM K109", "ROOM K101", "ROOM 138", "ROOM K104",
        "ROOM MH 2", "ROOM K110", "ROOM 304", "ROOM 137", "ROOM MH 1",
        "CDC ROOM 1", "ROOM 136", "ROOM 9", "Physio Counter 01",
        "ROOM PSY 2", "ROOM 303", "GP ROOM 1", "GP ROOM 2", "GP ROOM 3",
        "ROOM K108", "ROOM 133", "ROOM 134",
    ]

    entries = queue_data.get("data", [])

    # Only include entries with Pq of "1" or "0"
    filtered_entries = [
        entry for entry in entries
        if entry.get("Pq") in ("1", "0")
    ]

    if not filtered_entries:
        return "No matching room data found."

    token_lookup = {
        entry["RoomLabel"].strip().upper(): (
            str(entry["TokenNo"]),
            entry["Pq"],
            str(entry.get("RoomID", ""))
        )
        for entry in filtered_entries
    }

    static_rooms = [r.upper() for r in all_rooms]
    dynamic_rooms = [r for r in token_lookup if r not in static_rooms]
    combined = static_rooms + dynamic_rooms

    # Filter to only rooms present in token_lookup
    rooms_with_data = [
        room for room in combined if room in token_lookup
    ]

    sorted_rooms = sorted(rooms_with_data)

    groups = {}
    for room in sorted_rooms:
        token, pq, room_id = token_lookup[room]
        # Decide group title based on rules
        if len(room_id) == 1:
            group_key = "General OPD"
        elif "GP" in room:
            group_key = "Hulumale Phase 2 H16 Clinic"
        else:
            group_key = "Specialist OPD and Other Rooms"

        groups.setdefault(group_key, []).append((room, token, pq))

    # Build output text
    lines = []
    for group in sorted(groups):
        lines.append(group + ":")
        for room, token, pq in groups[group]:
            symbol = "❗" if pq == "1" else "🟩"
            lines.append(f"  {symbol} {room} | Token: {token}")
        lines.append("")

    return "\n".join(lines).strip()





'''
#******************************************JSON DEBUGGING*****************************************************
# uncomment to to test
import requests, time, json
AUTH_TOKEN = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiI5IiwianRpIjoiMGRjMDc3ZGNmOWJhM2JjMDAxYWE4YjUxMmM3MDZjZjIxZGFjNDlkMmQ1OTJlNDYxMWMxMmJiMTY3NjZiNzE3YTlhOTEyZGQyZWNhMTE0YzYiLCJpYXQiOjE3MzY2ODM1NjQuMjE5MTYyLCJuYmYiOjE3MzY2ODM1NjQuMjE5MTY0LCJleHAiOjE3NjgyMTk1NjQuMTkwNDQ0LCJzdWIiOiIiLCJzY29wZXMiOltdfQ.Yp-DePs9uK0C8ZtR5zbO4QQlfkZuVcFQsLQFj8RdCNXLX6fyhMyt6-EI0DAY89eHWGQf2IKUK0bAE1EU2ur10ODUbJKcqUtGCGGAaXY9L2h_ZGR08V3mCkf_xi3EmPzEpZ3sgZESgnGVB9gPp93rqeefXpOGKWfQwDeaW7zGAmew5nvNBZwYkTXfaFIJRZdCWQ_Qc-evuw-7iICqjgoWCn6rQGsKHpI1JBdCSPfgAgNy4kuK30xFN5nzQyCchiMIfnEzzClpV3xzhFd-HfV2Hk8WkPsE2UTNtsVFK7VweU9TQs58OZVrsGTBgmxdf8jMuB6T-4DgaRctaWkqasTsZa7WSk302FrtEF9fWWbpZY2l8XxtbwJMowIVGPBNfPyqD_tOYaZy0hBG5S3Q6GSRbg1ZRu5P63Gx8hSp7YMnRlEt4wy_CZMR0gzC4cs6RnUMgqUj-Q_VhV0BidGU8z6z4F5VENBbfbDFM-dYkEP5Ju09ghxXrT1-XGDPR4XKOzdWuiZOM1bwLlffpSDzygInX0Z-HNz6BMzK0LsOI0HlEPFl6V2bAcRH9g0jT4hwL0TnZTmlJpkwI2QQaGqM7d3bhqCnUzIgfediXywaJkPuYtqIm2-1Q7CJtp0P_-15mtFUaT8QUwHOs5_SKhS4IYZG0D6fjFpfv7HTH2DKe80X6Zs'
API_URL = 'https://api.hmh.gov.mv/api/queue/0'
JSON_FILE = 'queue_data.json'
# telegram links--------------------------------------------------------
TELEGRAM_BOT_TOKEN = '7883099850:AAFGMRnEZGE5vKH6CUMHyZMmyBu3Sdl0pts'
API_URL_BASE = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/'
# ------------------------------------------------------------------------
HEADERS = {
    'Accept': 'application/json',
    'authorization': AUTH_TOKEN
}
def fetch_data_from_api():
    """Fetches the latest queue data from the API and saves it to a JSON file."""
    resp = requests.get(API_URL, headers=HEADERS, timeout=10)
    try:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Fetched data, HTTP status: {resp.status_code}")
        resp.raise_for_status()
        data = resp.json()

        # Dump the data to a JSON file
        with open('queue_data.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        print("✅ Data saved to queue_data.json")
        return data

    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching data: {e}")
    except ValueError:
        print(f"❌ Could not decode JSON from response: {resp.text}")
    return None

fetch_data = fetch_data_from_api()

'''
