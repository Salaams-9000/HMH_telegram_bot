import requests, threading, time
from rooms import all_rooms_list_grouped

AUTH_TOKEN = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiI5IiwianRpIjoiMGRjMDc3ZGNmOWJhM2JjMDAxYWE4YjUxMmM3MDZjZjIxZGFjNDlkMmQ1OTJlNDYxMWMxMmJiMTY3NjZiNzE3YTlhOTEyZGQyZWNhMTE0YzYiLCJpYXQiOjE3MzY2ODM1NjQuMjE5MTYyLCJuYmYiOjE3MzY2ODM1NjQuMjE5MTY0LCJleHAiOjE3NjgyMTk1NjQuMTkwNDQ0LCJzdWIiOiIiLCJzY29wZXMiOltdfQ.Yp-DePs9uK0C8ZtR5zbO4QQlfkZuVcFQsLQFj8RdCNXLX6fyhMyt6-EI0DAY89eHWGQf2IKUK0bAE1EU2ur10ODUbJKcqUtGCGGAaXY9L2h_ZGR08V3mCkf_xi3EmPzEpZ3sgZESgnGVB9gPp93rqeefXpOGKWfQwDeaW7zGAmew5nvNBZwYkTXfaFIJRZdCWQ_Qc-evuw-7iICqjgoWCn6rQGsKHpI1JBdCSPfgAgNy4kuK30xFN5nzQyCchiMIfnEzzClpV3xzhFd-HfV2Hk8WkPsE2UTNtsVFK7VweU9TQs58OZVrsGTBgmxdf8jMuB6T-4DgaRctaWkqasTsZa7WSk302FrtEF9fWWbpZY2l8XxtbwJMowIVGPBNfPyqD_tOYaZy0hBG5S3Q6GSRbg1ZRu5P63Gx8hSp7YMnRlEt4wy_CZMR0gzC4cs6RnUMgqUj-Q_VhV0BidGU8z6z4F5VENBbfbDFM-dYkEP5Ju09ghxXrT1-XGDPR4XKOzdWuiZOM1bwLlffpSDzygInX0Z-HNz6BMzK0LsOI0HlEPFl6V2bAcRH9g0jT4hwL0TnZTmlJpkwI2QQaGqM7d3bhqCnUzIgfediXywaJkPuYtqIm2-1Q7CJtp0P_-15mtFUaT8QUwHOs5_SKhS4IYZG0D6fjFpfv7HTH2DKe80X6Zs'
API_URL = 'https://api.hmh.gov.mv/api/queue/0'
JSON_FILE = 'queue_data.json'
# telegram links--------------------------------------------------------
TELEGRAM_BOT_TOKEN = '-'
API_URL_BASE = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/'
# ------------------------------------------------------------------------
HEADERS = {
    'Accept': 'application/json',
    'authorization': AUTH_TOKEN
}
# globals:
sessions = {}  # chat_id


class Session:
    def __init__(self, chat_id):
        self.chat_id = chat_id
        self.stop_event = threading.Event()
        self.is_running = False
        self.thread = None
        self.selected_rooms = None  # or set() to default “all”
        self.current_fetch = None


# sending the text to the user function-----------------------------------------


def send_telegram_message(chat_id, message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML'
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(chat_id, message)
        if not response.ok:
            print(f"❌ Telegram API error: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Telegram send error: {e}")


def get_initial_offset():
    resp = requests.get(API_URL_BASE + "getUpdates", timeout=10).json().get("result", [])
    return (resp[-1]["update_id"] + 1) if resp else None


def start_monitoring(sess):
    sess.current_fetch = fetch_data_from_api()
    watch_queue(sess, poll_interval=15)


def handle_update(update):
    data = fetch_data_from_api()
    text = update["message"].get("text", "").strip().lower()
    chat_id = update["message"]["chat"]["id"]
    # get-or-create per-chat session
    sess = sessions.get(chat_id)

    if not sess:
        sess = Session(chat_id)
        sessions[chat_id] = sess
    print(f"Session({sess.chat_id}): Entered = {text}")
    if text in ("/start", "/begin") and not sess.is_running:
        sess.stop_event.clear()
        sess.thread = threading.Thread(target=start_monitoring, args=(sess,))
        sess.thread.start()
        sess.is_running = True
        send_telegram_message(chat_id, "✅ Monitoring started")
        send_telegram_message(chat_id, "---------------------------------------")  # remove this after the testing phase
        send_telegram_message(chat_id, "Greeting I am the HMH Queue monitor BOT")
        send_telegram_message(chat_id, "Here is the list of rooms that you can monitor")
        send_telegram_message(chat_id, all_rooms_list_grouped(data))
        send_telegram_message(chat_id, "❗= Priority Patient \n🟩 = Normal Patient \n🟨 = Room Closed")
        send_telegram_message(chat_id, "Current setting: List all changes")
    elif text.startswith("/room") and sess.is_running:
        # parse and set user_selected_rooms…
        send_telegram_message(chat_id, "feature is under construction 🚧")
        sess.selected_rooms = {
            r.strip().upper() for r in text[5:].split(",")
        }
        send_telegram_message(chat_id, f"Rooms set to: {sess.selected_rooms}")


    elif text == "/done" and sess.is_running:
        sess.stop_event.set()
        sess.thread.join()
        sess.is_running = False
        send_telegram_message(chat_id, "🛑 Monitoring stopped")


def watch_queue(sess, poll_interval=15):
    while not sess.stop_event.is_set():
        time.sleep(poll_interval)
        new = fetch_data_from_api()
        if new:
            diff_and_report(sess, sess.current_fetch, new)
            sess.current_fetch = new


def fetch_data_from_api():
    """Fetches the latest queue data from the API."""
    resp = requests.get(API_URL, headers=HEADERS, timeout=10)
    try:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Fetched data, HTTP status: {resp.status_code}")
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching data: {e}")
    except ValueError:
        print(f"❌ Could not decode JSON from response: {resp.text}")
    return None


def diff_and_report(sess, old, new):
    """
    Compare two fetch dicts (with key "data" → list of entries).
    Print out any additions/removals/changes per RoomLabel.
    """

    def prioritycheck(pqq):
        if pqq == "1":
            return "❗"  # priority patient
        elif pqq == "0":
            return "🟩"  # normal patient
        else:
            return "🟨"  # room closed or unknown

    old_list = old.get("data", []) if old else []
    new_list = new.get("data", []) if new else []

    # Build lookups by room label
    old_lookup = {e["RoomLabel"].strip().upper(): (e["TokenNo"], e["Pq"]) for e in old_list}
    new_lookup = {e["RoomLabel"].strip().upper(): (e["TokenNo"], e["Pq"]) for e in new_list}

    rooms = set(old_lookup) | set(new_lookup)
    changes = []

    for room in sorted(rooms):
        old_val = old_lookup.get(room)
        new_val = new_lookup.get(room)

        if old_val and not new_val:
            tok, pq = old_val
            changes.append(
                f"🚫 {room} Closed Last token:{tok} {prioritycheck(pq)}"
            )

        # Newly added
        elif not old_val and new_val:
            tok, pq = new_val
            changes.append(
                f"🆕 {room} Opened → {tok} {prioritycheck(pq)}"
            )

        # Changed token or priority
        elif old_val != new_val:
            old_tok, old_pq = old_val
            new_tok, new_pq = new_val
            changes.append(
                f"🔄 {room} changed: "
                f"{old_tok} {prioritycheck(old_pq)} → {new_tok} {prioritycheck(new_pq)}"
            )

    if changes:
        print("=== Changes detected ===")
        for line in changes:
            send_telegram_message(sess.chat_id, line)
    else:
        print("— No changes.")


def main():
    global LAST_UPDATE_ID
    LAST_UPDATE_ID = get_initial_offset()
    print("Waiting for /begin command...")
    while True:
        try:
            params = {"timeout": 10}
            if LAST_UPDATE_ID is not None:
                params["offset"] = LAST_UPDATE_ID

            resp = requests.get(API_URL_BASE + "getUpdates", params=params, timeout=15)

            # Safely parse JSON
            try:
                data = resp.json()
            except ValueError:
                print("❌ getUpdates returned invalid JSON:", resp.text)
                time.sleep(5)
                continue

            # Process each update
            for update in data.get("result", []):
                LAST_UPDATE_ID = update["update_id"] + 1
                handle_update(update)

        except requests.RequestException as e:
            print("Polling error:", e)
            time.sleep(5)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Bot manually stopped.")

# Salaams_D_sky
