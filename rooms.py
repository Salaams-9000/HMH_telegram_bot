#need to go through this again and count all the rooms. it is highly likely that I missed some rooms.
import re


def all_rooms_list_grouped(queue_data):
    """Builds a grouped list of rooms sorted by room name, with blank lines between similar-room groups."""
    if not queue_data:
        return "No queue data available."

    # Canonical list of rooms
    all_rooms = [
        "ROOM 8", "ROOM 5", "ROOM 7", "ROOM 6", "ROOM 301",
        "ROOM PSY 1", "ROOM K109", "ROOM K101", "ROOM 138", "ROOM K104",
        "ROOM MH 2", "ROOM K110", "ROOM 304", "ROOM 137", "ROOM MH 1",
        "CDC ROOM 1", "ROOM 136", "ROOM 9", "Physio Counter 01",
        "ROOM PSY 2", "ROOM 303", "GP ROOM 1", "GP ROOM 2", "GP ROOM 3",
        "ROOM K108", "ROOM 133", "ROOM 134",
    ]

    # Build lookup from API data
    entries = queue_data.get("data", [])
    token_lookup = {
        entry["RoomLabel"].strip().upper(): (str(entry["TokenNo"]), entry["Pq"])
        for entry in entries
    }

    # Combine static and any dynamic rooms seen
    static_rooms = [r.upper() for r in all_rooms]
    dynamic_rooms = [r for r in token_lookup if r not in static_rooms]
    combined = static_rooms + dynamic_rooms

    # Filter only rooms with Pq "1" or "0"
    rooms_with_data = [
        room for room in combined
        if token_lookup.get(room, (None, None))[1] in ("1", "0")
    ]

    # Sort alphabetically by full room name
    sorted_rooms = sorted(rooms_with_data)

    # Group by the text prefix before the numeric part
    pattern = re.compile(r"^([A-Z ]+?)(?=\s*\d+$)")
    groups = {}
    for room in sorted_rooms:
        m = pattern.match(room)
        group_key = m.group(1).strip() if m else room
        groups.setdefault(group_key, []).append(room)

    # Build the output with blank lines between groups
    lines = []
    for group in sorted(groups):
        lines.append(group + ":")
        for room in groups[group]:
            token, pq = token_lookup[room]
            symbol = "❗" if pq == "1" else "🟩"
            lines.append(f"  {symbol} {room} | Token: {token}")
        lines.append("")  # blank line between groups

    return "\n".join(lines).strip()