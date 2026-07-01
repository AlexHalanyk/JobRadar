from bot import send_notification

def is_relevant(job):
    return job["price"] >= 200

jobs = [
    {"route": "London -> Manchester", "cargo": "furniture", "price": 450, "link": "..."},
    {"route": "Leeds -> Bristol", "cargo": "boxes", "price": 120, "link": "..."},
    {"route": "Glasgow -> London", "cargo": "piano", "price": 600, "link": "..."}
]

for job in jobs:
    print(job["route"], job["price"])

for job in jobs:
    if is_relevant(job):
        send_notification(job)
        print("Sended:", job["route"])

