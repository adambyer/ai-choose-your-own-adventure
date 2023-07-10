"""Request handlers."""
import hashlib
import hmac
import json
import os

from src.chatgpt import get_story
from src.facebook import comment_on_post, get_post, get_comments, create_post

FACEBOOK_WEBHOOK_VERIFICATION_TOKEN = os.getenv("FACEBOOK_WEBHOOK_VERIFICATION_TOKEN")
FACEBOOK_APP_SECRET = os.getenv("FACEBOOK_APP_SECRET")
FACEBOOK_PAGE_ID = os.getenv("FACEBOOK_PAGE_ID")


def _get_post_content(messages=None):
    story = get_story(messages)
    return f"""{story}

    Add a comment with only the number of your choice.
    """


def handle_get_request(event):
    """Handle GET request."""
    print("*** handle_get_request")
    if event.get("createPost"):
        # Handle scheduled event to create daily story
        content = _get_post_content()
        create_post(content)
        return {
            "statusCode": 200,
        }

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
    """Handle POST request from FB (webhook events)."""
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

            # We only care about comments.
            if item == "comment":
                from_ = value.get("from")

                if not from_:
                    print("*** handle_post_request: no from")
                    continue

                _handle_comment_added(post_id, from_["id"], message)


def _handle_comment_added(post_id, from_id, message):
    """Handle new comment being added to FB page post."""
    print("*** _handle_comment_added:", post_id, from_id, message)
    message = message.lower()

    # We only care about comments that are a single int (choice).
    try:
        _ = int(message)
    except ValueError:
        print("*** _handle_comment_added: ignoring non-choice comment")
        return

    post = get_post(post_id)

    if not post:
        print("*** _handle_comment_added: post not found")
        return

    from_ = post.get("from")

    if not from_:
        print("*** _handle_comment_added: no from")
        return

    comments = get_comments(post_id)

    # Create ChatGPT messages from comments.
    # We only care about comments from either the page or the current commentor.
    # Page comments are assigned the assistant role, commentor comments are assigned the user role.
    # Also reversing since they come in oldest to newest.
    messages = [
        {
            "role": "user" if c["from"]["id"] == from_id else "assistant",
            "content": c["message"],
        }
        for c in comments
        if c["from"]["id"] in [from_id, FACEBOOK_PAGE_ID]
    ].reverse()

    # Append users choice.
    messages.append(
        {
            "role": "user",
            "content": message,
        }
    )

    comment = _get_post_content(messages)
    comment_on_post(post_id, comment)
