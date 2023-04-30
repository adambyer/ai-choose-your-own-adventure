"""Request handlers."""
import hashlib
import hmac
import json
import os

from src.chatgpt import get_story
from src.facebook import comment_on_post, get_post

FACEBOOK_WEBHOOK_VERIFICATION_TOKEN = os.getenv("FACEBOOK_WEBHOOK_VERIFICATION_TOKEN")
FACEBOOK_APP_SECRET = os.getenv("FACEBOOK_APP_SECRET")


def handle_get_request(event):
    """Handle incoming GET request from FB to webhook endpoint."""
    print("*** handle_get_request")
    # GET handles verification
    if event["requestContext"]["http"]["method"].upper() == "GET":
        params = event.get("queryStringParameters", {})
        mode = params.get("hub.mode")
        token = params.get("hub.verify_token")
        challenge = params.get("hub.challenge")

        if mode != "subscribe" or token != FACEBOOK_WEBHOOK_VERIFICATION_TOKEN:
            return {
                "statusCode": 400,
            }

        return {
            "statusCode": 200,
            "body": challenge,
        }

    return None


def handle_post_request(event):
    """Handle incoming POST request from FB to webhook endpoint."""
    print("*** handle_post")
    response = {
        "statusCode": 200,
    }

    body = event.get("body")

    if not body:
        print("*** handle_post_request: no body")
        return response

    headers = event.get("headers", {})
    signature = headers.get("x-hub-signature-256")

    if not signature:
        print("*** handle_post_request: no signature")
        return response

    _, signature_hash = signature.split("=")
    key = bytes(FACEBOOK_APP_SECRET, "utf-8")
    msg = bytes(body, "utf-8")
    expected_hash = hmac.new(key, msg=msg, digestmod=hashlib.sha256).hexdigest()
    body = json.loads(body)

    if expected_hash != signature_hash:
        print("*** handle_post_request: signature does not match")
        return response

    if "object" not in body or body["object"] != "page":
        print("*** handle_post_request: no/wrong object")
        return response

    if "entry" not in body:
        print("*** handle_post_request: no entry")
        return response

    for entry in body["entry"]:
        if "changes" not in entry:
            print("*** handle_post_request: no changes")
            continue

        for change in entry["changes"]:
            if "value" not in change:
                print("*** handle_post_request: no value")
                continue

            value = change["value"]

            if "item" not in value:
                print("*** handle_post_request: no item")
                continue

            item = value["item"]

            if "verb" not in value:
                print("*** handle_post_request: no verb")
                continue

            if "post_id" not in value:
                print("*** handle_post_request: no post_id")
                continue

            post_id = value["post_id"]

            # What action was taken?
            verb = value["verb"]

            # We only care about creations.
            if verb != "add":
                print("*** handle_post_request: verb not add")
                continue

            message = value.get("message")

            if not message:
                continue

            # What type of update was this?
            if item == "status":
                _handle_post_added(post_id, message)
            elif item == "comment":
                from_ = value.get("from")

                if not from_:
                    print("*** handle_post_request: no from")
                    continue

                _handle_comment_added(post_id, from_["id"], message)

    return None


def _handle_post_added(post_id, message):
    """Handle new post being added to FB page."""
    print("*** _handle_post_added:", post_id, message)
    if not message.lower().startswith("start"):
        print("*** _handle_post_added: not a 'start' message")
        return

    # Create a comment on the new post.
    comment = get_story()
    comment_on_post(post_id, comment)


def _handle_comment_added(post_id, from_id, message):
    """Handle new comment being added to FB page post."""
    print("*** _handle_comment_added:", post_id, from_id, message)
    message = message.lower()

    try:
        choice = int(message)
    except ValueError:
        print("*** _handle_comment_added: invalid choice")
        return

    post = get_post(post_id)

    if not post:
        print("*** _handle_comment_added: post not found")
        return

    from_ = post.get("from")

    if not from_:
        print("*** _handle_comment_added: no from")
        return

    post_from_id = from_["id"]

    if post_from_id != from_id:
        # Comment is not from the original poster. Ignore.
        print("*** _handle_comment_added: comment not from original poster")
        return

    print("*** _handle_comment_added: all good, get next part of story", choice)
