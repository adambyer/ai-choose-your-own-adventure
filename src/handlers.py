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
    print("*** handle_post_request")
    body = event.get("body")

    if not body:
        print("*** handle_post_request: no body")
        return

    headers = event.get("headers", {})
    signature = headers.get("x-hub-signature-256")

    if not signature:
        print("*** handle_post_request: no signature")
        return

    _, signature_hash = signature.split("=")
    key = bytes(FACEBOOK_APP_SECRET, "utf-8")
    msg = bytes(body, "utf-8")
    expected_hash = hmac.new(key, msg=msg, digestmod=hashlib.sha256).hexdigest()
    body = json.loads(body)

    if expected_hash != signature_hash:
        print("*** handle_post_request: signature does not match")
        return

    if "object" not in body or body["object"] != "page":
        print("*** handle_post_request: no/wrong object")
        return

    if "entry" not in body:
        print("*** handle_post_request: no entry")
        return

    for entry in body["entry"]:
        if "changes" not in entry:
            print("*** handle_post_request: no changes")
            continue

        for change in entry["changes"]:
            value = change.get("value")
            if not value:
                print("*** handle_post_request: no value")
                continue

            item = value.get("item")
            if not item:
                print("*** handle_post_request: no item")
                continue

            verb = value.get("verb")
            if verb != "add":
                # We only care about creations.
                print("*** handle_post_request: verb not add")
                continue

            post_id = value.get("post_id")
            if not post_id:
                print("*** handle_post_request: no post_id")
                continue

            message = value.get("message")

            if not message:
                print("*** handle_post_request: no message")
                continue

            # What type of update was this?
            if item == "status":
                _handle_post_added(post_id, message)
            elif item == "comment":
                from_ = value.get("from")

                if not from_:
                    print("*** handle_post_request: no from")
                    continue

                if value.get("comment_id"):
                    # Just ignore replies to comments
                    continue

                _handle_comment_added(post_id, from_["id"], message)


def _handle_post_added(post_id, message):
    """Handle new post being added to FB page."""
    print("*** _handle_post_added:", post_id, message)
    if not message.lower().startswith("start"):
        print("*** _handle_post_added: not a 'start' message")
        return

    # Create a comment on the new post.
    story = get_story()
    comment = f"""{story}

    Add a comment (not a reply) with only the number.
    """
    comment_on_post(post_id, comment)


def _handle_comment_added(post_id, from_id, message):
    """Handle new comment being added to FB page post."""
    print("*** _handle_comment_added:", post_id, from_id, message)
    message = message.lower()

    try:
        choice = int(message)
    except ValueError:
        print("*** _handle_comment_added: invalid choice")
        # TODO: this will also weed out the replies made by the system, but should have a better way.
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
