import requests
def all_rooms_list_grouped(queue_data, mode):
    """Builds a grouped list of rooms, filtered by `mode`."""
    if not queue_data:
        return "No queue data available."

    # normalize mode key
    mode_key = mode.lstrip("/").lower()
    # map mode → the exact group title in output
    mode_to_title = {
        "general_opd":        "General OPD",
        "phase_2_h16":        "Hulumale Phase 2 H16 Clinic",
        "specialist_opd":     "Specialist OPD and Other Rooms",
        "all":                None,  # None means “don’t filter”
    }
    target_title = mode_to_title.get(mode_key, None)

    all_rooms = [
        "ROOM 8", "ROOM 5", "ROOM 7", "ROOM 6", "ROOM 301",
        "ROOM PSY 1", "ROOM K109", "ROOM K101", "ROOM 138", "ROOM K104",
        "ROOM MH 2", "ROOM K110", "ROOM 304", "ROOM 137", "ROOM MH 1",
        "CDC ROOM 1", "ROOM 136", "ROOM 9", "Physio Counter 01",
        "ROOM PSY 2", "ROOM 303", "GP ROOM 1", "GP ROOM 2", "GP ROOM 3",
        "ROOM K108", "ROOM 133", "ROOM 134",
    ]

    entries = queue_data.get("data", [])
    filtered = [e for e in entries if e.get("Pq") in ("1", "0")]
    if not filtered:
        return "No matching room data found."

    # build lookup: UPPER label → (token, pq, room_id)
    token_lookup = {
        e["RoomLabel"].strip().upper(): (
            str(e["TokenNo"]), e["Pq"], str(e.get("RoomID", "")))
        for e in filtered
    }

    static_rooms = [r.upper() for r in all_rooms]
    dynamic_rooms = [r for r in token_lookup if r not in static_rooms]
    combined = static_rooms + dynamic_rooms
    rooms_with_data = [r for r in combined if r in token_lookup]
    sorted_rooms = sorted(rooms_with_data)

    # grouping
    groups = {}
    for room in sorted_rooms:
        token, pq, room_id = token_lookup[room]

        # determine lower‐case group key
        def get_group(rid, lbl):
            if len(str(rid)) == 1:
                return "general opd"
            elif "GP" in lbl:
                return "phase 2 h16"
            else:
                return "specialist opd"

        grp_key = get_group(room_id, room)
        # map to title exactly as we’ll print it
        if grp_key == "general opd":
            title = "General OPD"
        elif grp_key == "phase 2 h16":
            title = "Hulumale Phase 2 H16 Clinic"
        else:
            title = "Specialist OPD and Other Rooms"

        groups.setdefault(title, []).append((room, token, pq))

    # build the text, filtering by target_title if set
    lines = []
    for title in sorted(groups):
        if target_title and title != target_title:
            continue

        lines.append(f"{title}:")
        for room, token, pq in groups[title]:
            sym = "❗" if pq == "1" else "🟩"
            lines.append(f"  {sym} {room} | Token: {token}")
        lines.append("")

    output = "\n".join(lines).strip()
    return output if output else "No rooms match that mode."






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
