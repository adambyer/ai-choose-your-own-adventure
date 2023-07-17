"""Request handlers."""
import json
import os
import re

from .enums import PromptRole
from .facebook import create_comment, get_post_or_comment, get_comments, create_post
from .openai import get_story

FACEBOOK_PAGE_ID = os.getenv("FACEBOOK_PAGE_ID")


def _get_post_content(messages=None):
    instructions = f"*** Add a {'reply' if messages else 'comment'} with the number of your choice. ***"
    story = get_story(messages)
    part = len([m for m in messages if m["role"] == PromptRole.ASSISTANT]) + 1 if messages else 1

    # AI seems to add these when it sees them in the history.
    if "*** PART" not in story:
        story = f"*** PART {part} ***\n\n {story}"
    if "with the number of your choice" not in story:
        story = f"{story} \n\n {instructions}"

    return story


def handle_request(event):
    print("*** handle_request: event", event)

    if event.get("create-story"):
        content = _get_post_content()
        create_post(content)
        return {
            "statusCode": 200,
        }

    body = event.get("body")

    if not body:
        print("*** handle_post_request: no body")
        return

    body = json.loads(body)

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

            # Confirm we have required values.
            ok = True
            for key in [
                "item",
                "verb",
                "post_id",
                "parent_id",
                "message",
            ]:
                if not value.get(key):
                    print(f"*** handle_post_request: no {key}")
                    ok = False

            if not ok:
                continue

            # We only care about comments.
            if value.get("item") != "comment":
                print("*** handle_post_request: item not comment")
                continue

            # We only care about creations.
            if value.get("verb") != "add":
                print("*** handle_post_request: verb not add")
                continue

            post_id = value.get("post_id")
            message = value.get("message")

            # Now confirm we have required comment values.
            ok = True
            for key in ["from", "comment_id", "parent_id"]:
                if not value.get(key):
                    print(f"*** handle_post_request: no {key}")
                    ok = False

            if not ok:
                continue

            from_ = value.get("from")
            comment_id = value.get("comment_id")
            parent_id = value.get("parent_id")

            _handle_comment_added(post_id, comment_id, parent_id, from_, message)


def _handle_comment_added(post_id, comment_id, parent_id, from_, message):
    """Handle new comment being added to FB page post."""
    message = message.lower()
    from_id = from_["id"]

    # We don't care about our own posts.
    if from_id == FACEBOOK_PAGE_ID:
        print("*** _handle_comment_added: ignnoring post from page account.", post_id, comment_id, parent_id, from_)
        return

    # Take the first integer from the comment for the choice.
    match = re.search(r"\b\d+\b", message)

    if not match:
        print("*** _handle_comment_added: ignoring non-choice comment.", post_id, comment_id, parent_id, from_, message)
        return

    choice = match.group()

    print("*** _handle_comment_added: have choice", post_id, comment_id, parent_id, from_, message, choice)

    post = get_post_or_comment(post_id)

    # If the post no longer exists just ignore.
    if not post:
        print("*** _handle_comment_added: post not found")
        return

    comments = []

    # Start with original post (beginning of story).
    messages = [
        {
            "role": PromptRole.ASSISTANT.value,
            "content": post["message"],
        },
    ]

    # We need to always add the new new comment to the first comment from the user
    # (ie. the one added directly to the story post).
    # If this is not the first comment, we'll find it below.
    initial_comment_id = comment_id

    if parent_id == post_id:
        # This is a comment on the original post; add the users choice.
        messages.append(
            {
                "role": PromptRole.USER.value,
                "content": choice,
            }
        )
    else:
        # This is a comment on a comment(COC).
        # First fetch the initial comment on the post
        initial_comment = get_post_or_comment(parent_id)

        # If the initial comment no longer exists just ignore.
        if not initial_comment:
            print("*** _handle_comment_added: initial comment not found")
            return

        # We only care about COCs if the from id of the COC matches the initial comment.
        if initial_comment["from"]["id"] != from_id:
            print("*** _handle_comment_added: comment on comment from different user")
            return

        messages.append(
            {
                "role": PromptRole.USER.value,
                "content": initial_comment["message"],
            }
        )

        initial_comment_id = initial_comment["id"]

        # Fetch the COC thread of the initial comment.
        comments = get_comments(initial_comment_id)

        print("*** _handle_comment_added: comments", comments)

        # Create AI messages from comments.
        # We only care about comments from either the page or the current commentor.
        # Page comments are assigned the assistant role, commentor comments are assigned the user role.
        for c in comments:
            if c["from"]["id"] in [from_id, FACEBOOK_PAGE_ID]:
                messages.append(
                    {
                        "role": PromptRole.USER.value if c["from"]["id"] == from_id else PromptRole.ASSISTANT.value,
                        "content": c["message"],
                    }
                )

    print("*** _handle_comment_added: messages", messages)

    comment = _get_post_content(messages)
    create_comment(initial_comment_id, comment)
