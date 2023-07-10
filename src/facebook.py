import os
import requests

FACEBOOK_ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN")
FACEBOOK_PAGE_ID = os.getenv("FACEBOOK_PAGE_ID")


def get_post(post_id):
    print("*** get_post")
    url = f"https://graph.facebook.com/{post_id}"
    payload = {
        "access_token": FACEBOOK_ACCESS_TOKEN,
        "fields": "from",
    }
    response = requests.get(url, data=payload)

    if response.status_code == 200:
        print("*** get_post: succes", response.status_code)
        return response.json()

    print("*** get_post: error", response.status_code, response.text)
    return None


def create_post(content):
    print("*** comment_on_post")
    url = f"https://graph.facebook.com/{FACEBOOK_PAGE_ID}/feed"
    payload = {"message": content, "access_token": FACEBOOK_ACCESS_TOKEN}
    response = requests.post(url, data=payload)

    if response.status_code == 200:
        print("*** create_post: succes", response.status_code)
    else:
        print("*** create_post: error", response.status_code, response.text)


def get_comments(post_id):
    print("*** get_comments")
    url = f"https://graph.facebook.com/{post_id}/comments"
    payload = {
        "access_token": FACEBOOK_ACCESS_TOKEN,
    }
    response = requests.get(url, data=payload)

    if response.status_code == 200:
        print("*** get_comments: succes", response.status_code)
        return response.json()["data"]

    print("*** get_comments: error", response.status_code, response.text)
    return None


def comment_on_post(post_id, content):
    print("*** comment_on_post")
    url = f"https://graph.facebook.com/{post_id}/comments"
    payload = {"message": content, "access_token": FACEBOOK_ACCESS_TOKEN}
    response = requests.post(url, data=payload)

    if response.status_code == 200:
        print("*** comment_on_post: succes", response.status_code)
    else:
        print("*** comment_on_post: error", response.status_code, response.text)
