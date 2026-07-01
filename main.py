from bot import send_notification, is_relevant_ai


def is_relevant(job):
    return job["price"] >= 200


jobs = [
    {"route": "London -> Manchester", "cargo": "furniture", "price": 450, "link": "..."},
    {"route": "Leeds -> Bristol", "cargo": "boxes", "price": 120, "link": "..."},
    {"route": "Glasgow -> London", "cargo": "piano", "price": 600, "link": "..."}
]

for job in jobs:
    if not is_relevant(job):
        print("Skip (cheap filter):", job["route"])
        continue

    if is_relevant_ai(job):
        send_notification(job)
        print("Sent (AI approved):", job["route"])
    else:
        print("Skip (AI rejected):", job["route"])