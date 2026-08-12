from memory import get_open_escalations

escalations = get_open_escalations()

if not escalations:
    print("No open escalation requests.")
else:
    print("\n=== Open Human Help Requests ===\n")
    for esc in escalations:
        print(f"Reference ID : {esc['reference_id']}")
        print(f"Name         : {esc['name']}")
        print(f"Reason       : {esc['reason']}")
        print(f"Summary      : {esc['summary']}")
        print(f"Urgency      : {esc['urgency']}")
        print(f"Created at   : {esc['created_at']}")
        print("-" * 40)