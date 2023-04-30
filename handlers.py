"""Request handlers."""
import json
import os

from chatgpt import get_story
from facebook import comment_on_post, get_post

TOKEN = os.getenv("WEBHOOK_VERIFICATION_TOKEN")


def handle_get(event):
    print("*** handle_get")
    # GET handles verification
    if event["requestContext"]["http"]["method"].upper() == "GET":
        params = event.get("queryStringParameters", {})
        mode = params.get("hub.mode")
        token = params.get("hub.verify_token")
        challenge = params.get("hub.challenge")

        if mode != "subscribe" or token != TOKEN:
            return {
                "statusCode": 400,
            }

        return {
            "statusCode": 200,
            "body": challenge,
        }

    return None


def handle_post(event):
    # TODO: validate payload with SHA256
    print("*** handle_post")
    response = {
        "statusCode": 200,
    }

    if "body" not in event:
        print("*** handle_post: no body")
        return response

    body = json.loads(event["body"])

    if "object" not in body or body["object"] != "page":
        print("*** handle_post: no/wrong object")
        return response

    if "entry" not in body:
        print("*** handle_post: no entry")
        return response

    for entry in body["entry"]:
        if "changes" not in entry:
            print("*** handle_post: no changes")
            continue

        for change in entry["changes"]:
            if "value" not in change:
                print("*** handle_post: no value")
                continue

            value = change["value"]

            if "item" not in value:
                print("*** handle_post: no item")
                continue

            item = value["item"]

            if "verb" not in value:
                print("*** handle_post: no verb")
                continue

            if "post_id" not in value:
                print("*** handle_post: no post_id")
                continue

            post_id = value["post_id"]

            # What action was taken?
            verb = value["verb"]

            # We only care about creations.
            if verb != "add":
                print("*** handle_post: verb not add")
                continue

            message = value.get("message")

            if not message:
                continue

            # What type of update was this?
            if item == "status":
                _handle_post(post_id, message)
            elif item == "comment":
                from_ = value.get("from")

                if not from_:
                    print("*** handle_post: no from")
                    continue

                _handle_comment(post_id, from_["id"], message)

    return None


def _handle_post(post_id, message):
    if not message.lower().startswith("new game"):
        return

    # Create a comment on the new post.
    comment = get_story()
    comment_on_post(post_id, comment)


def _handle_comment(post_id, from_id, message):
    message = message.lower()

    if not message.startswith("move:"):
        # Not a move comment. Just ignore.
        return

    post = get_post(post_id)

    if not post:
        print("*** _handle_move: post not found")
        return

    from_ = post.get("from")

    if not from_:
        print("*** _handle_move: no from")
        return

    post_from_id = from_["id"]

    if post_from_id != from_id:
        # Comment is not from the original poster. Ignore.
        return
