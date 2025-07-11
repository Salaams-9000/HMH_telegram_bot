from venv import logger

import requests, threading, time
from rooms import all_rooms_list_grouped

AUTH_TOKEN = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiI5IiwianRpIjoiMGRjMDc3ZGNmOWJhM2JjMDAxYWE4YjUxMmM3MDZjZjIxZGFjNDlkMmQ1OTJlNDYxMWMxMmJiMTY3NjZiNzE3YTlhOTEyZGQyZWNhMTE0YzYiLCJpYXQiOjE3MzY2ODM1NjQuMjE5MTYyLCJuYmYiOjE3MzY2ODM1NjQuMjE5MTY0LCJleHAiOjE3NjgyMTk1NjQuMTkwNDQ0LCJzdWIiOiIiLCJzY29wZXMiOltdfQ.Yp-DePs9uK0C8ZtR5zbO4QQlfkZuVcFQsLQFj8RdCNXLX6fyhMyt6-EI0DAY89eHWGQf2IKUK0bAE1EU2ur10ODUbJKcqUtGCGGAaXY9L2h_ZGR08V3mCkf_xi3EmPzEpZ3sgZESgnGVB9gPp93rqeefXpOGKWfQwDeaW7zGAmew5nvNBZwYkTXfaFIJRZdCWQ_Qc-evuw-7iICqjgoWCn6rQGsKHpI1JBdCSPfgAgNy4kuK30xFN5nzQyCchiMIfnEzzClpV3xzhFd-HfV2Hk8WkPsE2UTNtsVFK7VweU9TQs58OZVrsGTBgmxdf8jMuB6T-4DgaRctaWkqasTsZa7WSk302FrtEF9fWWbpZY2l8XxtbwJMowIVGPBNfPyqD_tOYaZy0hBG5S3Q6GSRbg1ZRu5P63Gx8hSp7YMnRlEt4wy_CZMR0gzC4cs6RnUMgqUj-Q_VhV0BidGU8z6z4F5VENBbfbDFM-dYkEP5Ju09ghxXrT1-XGDPR4XKOzdWuiZOM1bwLlffpSDzygInX0Z-HNz6BMzK0LsOI0HlEPFl6V2bAcRH9g0jT4hwL0TnZTmlJpkwI2QQaGqM7d3bhqCnUzIgfediXywaJkPuYtqIm2-1Q7CJtp0P_-15mtFUaT8QUwHOs5_SKhS4IYZG0D6fjFpfv7HTH2DKe80X6Zs'
API_URL = 'https://api.hmh.gov.mv/api/queue/0'
# telegram links--------------------------------------------------------
TELEGRAM_BOT_TOKEN = ''
API_URL_BASE = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/'
Strelitzias_token = '' #the wacther
Strelitzias_URL = f'https://api.telegram.org/bot{Strelitzias_token}/'
Creator = '2071852708'
# ------------------------------------------------------------------------
HEADERS = {
    'Accept': 'application/json',
    'authorization': AUTH_TOKEN
}


# FUNCTIONS NOTIFYING THE CREATOR IF THERE IS ANY ISSUE CALLING THE DATA FROM THE WEBSITE


# globals:
sessions = {}  # chat_id
class Session:
    def __init__(self, chat_id):
        self.chat_id = chat_id
        self.stop_event = threading.Event()
        self.is_running = False
        self.thread = None
        # New: track mode; default to list everything
        self.selected_rooms = "/all"
        self.current_fetch = None


def send_telegram_message(chat_id, message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML'
    }
    try:
        response = requests.post(url, json=payload, timeout=20)
        print(chat_id, message)
        if not response.ok:
            print(f"❌ Telegram API error: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Telegram send error: {e}")

def strelitzias_words(chat_id, message):
    url = f"https://api.telegram.org/bot{Strelitzias_token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML'
    }
    try:
        response = requests.post(url, json=payload, timeout=20)
        print(chat_id, message)
        if not response.ok:
            print(f"❌ Telegram API error: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Telegram send error: {e}")


def get_initial_offset():
    resp = requests.get(API_URL_BASE + "getUpdates", timeout=20).json().get("result", [])
    return (resp[-1]["update_id"] + 1) if resp else None


def start_monitoring(sess):
    sess.current_fetch = fetch_data_from_api()
    watch_queue(sess, poll_interval=20)


def handle_update(update):
    data = fetch_data_from_api()
    text = update["message"].get("text", "").strip().lower()
    chat_id = update["message"]["chat"]["id"]
    user = update["message"]["from"]
    user_name = user.get("username") or user.get("first_name", "unknown")

    # get-or-create per-chat session
    sess = sessions.get(chat_id)
    if not sess:
        sess = Session(chat_id)
        sessions[chat_id] = sess

    print(f"Session({sess.chat_id}): Entered = {text}")

    # START / BEGIN
    if text in ("/start", "/begin") and not sess.is_running:
        sess.selected_rooms = "/all"

        sess.stop_event.clear()
        sess.thread = threading.Thread(target=start_monitoring, args=(sess,))
        sess.thread.start()
        sess.is_running = True
        sess.mode = "/all"
        # ─── ADMIN NOTIFICATION ─────────────────────────────
        strelitzias_words(
            Creator,
            f"🔔 Session STARTED by @{user_name} (chat_id {chat_id})"
        )
        # ─────────────────────────────────────────────────────
        send_telegram_message(chat_id, "✅ Monitoring started")
        send_telegram_message(chat_id, all_rooms_list_grouped(data, sess.mode))
        send_telegram_message(chat_id,
            "❗= Priority Patient \n🟩 = Normal Patient \n🟨 = Room Closed\n"
            "Current setting: List ALL changes"
        )
    elif text.startswith("/all") and sess.is_running:
        sess.selected_rooms = "/all"
        sess.mode = "/all"
        send_telegram_message(chat_id,
            "✅ Settings changed: Listing ALL changes"
        )
        send_telegram_message(chat_id, all_rooms_list_grouped(data, sess.mode))

    elif text.startswith("/general_opd") and sess.is_running:
        sess.selected_rooms = "/general_opd"
        sess.mode = "/general_opd"
        send_telegram_message(chat_id,
            "✅ Settings changed: Listing ONLY General OPD rooms"
        )
        send_telegram_message(chat_id, all_rooms_list_grouped(data, sess.mode))

    elif text.startswith("/phase_2_h16") and sess.is_running:
        sess.selected_rooms = "/phase 2 h16"
        sess.mode = "/phase_2_h16"
        send_telegram_message(chat_id,
            "✅ Settings changed: Listing ONLY Phase 2 H16 Clinic rooms"
        )
        send_telegram_message(chat_id, all_rooms_list_grouped(data, sess.mode))

    elif text.startswith("/specialist_opd") and sess.is_running:
        sess.selected_rooms = "/specialist_opd"
        sess.mode = "/specialist_opd"
        send_telegram_message(chat_id,
            "✅ Settings changed: Listing ONLY Specialist OPD & other rooms"
        )
        send_telegram_message(chat_id, all_rooms_list_grouped(data, sess.mode))

    # STOP
    elif text == "/done" and sess.is_running:
        sess.stop_event.set()
        sess.thread.join()
        sess.is_running = False
        send_telegram_message(chat_id, "🛑 Monitoring stopped")
        # ─── ADMIN NOTIFICATION ─────────────────────────────
        strelitzias_words(
            Creator,
            f"🔔 Session ENDED by @{user_name} (chat_id {chat_id})"
        )
        # ─────────────────────────────────────────────────────


def watch_queue(sess, poll_interval=20):
    try:
        while not sess.stop_event.is_set():
            time.sleep(poll_interval)
            new = fetch_data_from_api()
            if new:
                diff_and_report(sess, sess.current_fetch, new, sess.selected_rooms)
                sess.current_fetch = new
    except Exception as e:
        logger.error("Watch Loop Crashed", exc_info=e)


def fetch_data_from_api():
    """Fetches the latest queue data from the API."""
    resp = requests.get(API_URL, headers=HEADERS, timeout=20)
    try:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Fetched data, HTTP status: {resp.status_code}")
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"❌ [{time.strftime('%Y-%m-%d %H:%M:%S')}]Error fetching data: {e}")
    return None


def diff_and_report(sess, old, new, mode):
    """
    Compare two fetch dicts and report additions/removals/changes
    but only for rooms matching `mode`.
    Modes: "/all", "/general opd", "/phase 2 h16", "/specialist opd".
    """

    def priority_symbol(pq):
        return "❗" if pq == "1" else "🟩" if pq == "0" else "🟨"

    def get_group(room_id, room_label):
        # same grouping rules as all_rooms_list_grouped :contentReference[oaicite:1]{index=1}
        if len(str(room_id)) == 1:
            return "general opd"
        elif "GP" in room_label:
            return "phase 2 h16"
        else:
            return "specialist opd"

    # Normalize mode key
    mode_key = mode.lstrip("/").lower()

    old_entries = old.get("data", []) if old else []
    new_entries = new.get("data", []) if new else []

    old_lookup = {
        e["RoomLabel"].strip().upper(): (e["TokenNo"], e["Pq"], e.get("RoomID"))
        for e in old_entries
    }
    new_lookup = {
        e["RoomLabel"].strip().upper(): (e["TokenNo"], e["Pq"], e.get("RoomID"))
        for e in new_entries
    }

    all_rooms = sorted(set(old_lookup) | set(new_lookup))
    changes = []

    for room in all_rooms:
        old_val = old_lookup.get(room)
        new_val = new_lookup.get(room)

        # Determine this room's group
        room_id = (new_val or old_val)[2]
        group = get_group(room_id, room)

        # Skip if mode is not "/all" and group ≠ mode
        if mode_key != "all" and group != mode_key:
            continue

        if old_val and not new_val:
            tok, pq, _ = old_val
            changes.append(f"🚫 {room} Closed | Last token:{tok} {priority_symbol(pq)}")

        elif not old_val and new_val:
            tok, pq, _ = new_val
            changes.append(f"🆕 {room} Opened → {tok} {priority_symbol(pq)}")

        elif old_val and new_val and old_val[:2] != new_val[:2]:
            old_tok, old_pq, _ = old_val
            new_tok, new_pq, _ = new_val
            changes.append(
                f"🔄 {room} changed: "
                f"{old_tok} {priority_symbol(old_pq)} → {new_tok} {priority_symbol(new_pq)}"
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
    print("Waiting for /start command...")
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