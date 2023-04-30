import os
import requests

FACEBOOK_ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN")


def get_post(post_id):
    print("*** get_post")
    url = f"https://graph.facebook.com/{post_id}"
    payload = {
        "access_token": FACEBOOK_ACCESS_TOKEN,
        "fields": "from",
    }
    response = requests.get(url, data=payload)

    if response.status_code == 200:
        print("*** succesfully posted to facebook", response.status_code)
        return response.json()

    print("*** error posting to facebook", response.status_code, response.text)
    return None


def comment_on_post(post_id, content):
    print("*** comment_on_post")
    url = f"https://graph.facebook.com/{post_id}/comments"
    payload = {"message": content, "access_token": FACEBOOK_ACCESS_TOKEN}
    response = requests.post(url, data=payload)

    if response.status_code == 200:
        print("*** succesfully posted to facebook", response.status_code)
    else:
        print("*** error posting to facebook", response.status_code, response.text)
