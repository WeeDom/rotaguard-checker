#! /usr/bin/env python3

# fetch_roster.py
from deputy_api import get_deputy
from datetime import datetime, timedelta
import json
from collections import defaultdict

def fetch_roster(start=None, end=None):
    params = {}
    if start:
        params["startTime"] = start.isoformat()
    if end:
        params["endTime"] = end.isoformat()

    # print("[*] Fetching roster...")
    data = get_deputy("/api/v1/supervise/roster")#, params=params)
    # print("[+] Fetched roster data successfully.") if data else print("[-] No data received.")

    # Group shifts by employee ID
    shifts_by_employee = defaultdict(list)
    for entry in data:
        employee_id = entry.get("_DPMetaData", {}).get("EmployeeInfo", {}).get("Id", "Unknown")
        name = entry.get("_DPMetaData", {}).get("EmployeeInfo", {}).get("DisplayName", "Unknown")
        start = entry.get("StartTimeLocalized", "N/A")
        end = entry.get("EndTimeLocalized", "N/A")

        if start != "N/A" and end != "N/A":
            start_dt = datetime.fromisoformat(start)
            end_dt = datetime.fromisoformat(end)
            shifts_by_employee[employee_id].append((name, start_dt, end_dt))

    # Print shifts and calculate breaks
    for employee_id, shifts in shifts_by_employee.items():
        shifts.sort(key=lambda x: x[1])  # Sort shifts by start time
        for i, (name, start_dt, end_dt) in enumerate(shifts):
            day = start_dt.strftime("%a %d")
            start_time = start_dt.strftime("%H:%M")
            end_time = end_dt.strftime("%H:%M")
            shift_length = (end_dt - start_dt).seconds // 3600  # Calculate shift length in hours

            # Check if the shift is a SPLIT
            split_marker = ""
            if i < len(shifts) - 1:
                next_start = shifts[i + 1][1]
                if start_dt.date() == next_start.date():
                    split_marker = " (SPLIT)"

            print(f"{name} - {day} {start_time} - {end_time} ({shift_length} hrs){split_marker}")

            # Calculate break length if there's a next shift
            if i < len(shifts) - 1:
                next_start = shifts[i + 1][1]
                # Only consider breaks between different days as potential illegal breaks
                if end_dt.date() != next_start.date():
                    break_length = (next_start - end_dt).seconds // 3600  # Break length in hours
                    if break_length < 11:
                        print(f"(break: {break_length} hrs) (ILLEGAL)")
                    else:
                        print(f"(break: {break_length} hrs)")

    # # You can dump the full result if needed:
    # print(json.dumps(data[0], indent=2))

if __name__ == "__main__":
    today = datetime.now()
    one_month_ago = today - timedelta(days=30)
    tomorrow = today + timedelta(days=1)
    fetch_roster(start=one_month_ago, end=today)
