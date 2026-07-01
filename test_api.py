import requests

response = requests.get("https://jsonplaceholder.typicode.com/posts")
posts = response.json()

print("Скільки прийшло:", len(posts))

for post in posts[:3]:
    print(post["id"], post["title"])

def is_relevant(post):
    return post["userId"] == 1

for post in posts:
    if is_relevant(post):
        print("Підходить:", post["id"], post["title"])