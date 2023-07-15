import hashlib
import hmac
import json
import os

import boto3

FACEBOOK_APP_SECRET = os.getenv("FACEBOOK_APP_SECRET")
FACEBOOK_WEBHOOK_VERIFICATION_TOKEN = os.getenv("FACEBOOK_WEBHOOK_VERIFICATION_TOKEN")


def lambda_handler(event, context):
    """Handle incoming requests from FB (webhook events) or EventBridge (scheduled events).

    - create-story comes from EventBridge
    """
    print("*** lambda_handler", event)

    if event.get("create-story") == FACEBOOK_WEBHOOK_VERIFICATION_TOKEN:
        print("*** lambda_handler: create story ok")
        pass
    elif event["requestContext"]["http"]["method"].upper() == "GET":
        # Handle verification request from Facebook.
        params = event.get("queryStringParameters", {})
        mode = params.get("hub.mode")
        token = params.get("hub.verify_token")
        challenge = params.get("hub.challenge")

        if mode != "subscribe" or token != FACEBOOK_WEBHOOK_VERIFICATION_TOKEN:
            print("*** lambda_handler: Facebook challenge failed")
            return {
                "statusCode": 401,
            }

        print("*** lambda_handler: Facebook challenge succeeded")
        return {
            "statusCode": 200,
            "body": challenge,
        }
    elif event["requestContext"]["http"]["method"].upper() == "POST":
        body = event.get("body")

        if not body:
            print("*** lambda_handler: no POST body")
            return {
                "statusCode": 400,
            }

        headers = event.get("headers", {})
        signature = headers.get("x-hub-signature-256")

        if not signature:
            print("*** lambda_handler: no Facebook signature")
            return {
                "statusCode": 400,
            }

        _, signature_hash = signature.split("=")
        key = bytes(FACEBOOK_APP_SECRET, "utf-8")
        msg = bytes(body, "utf-8")
        expected_hash = hmac.new(key, msg=msg, digestmod=hashlib.sha256).hexdigest()
        body = json.loads(body)

        if expected_hash != signature_hash:
            print("*** lambda_handler: Facebook signature does not match")
            return {
                "statusCode": 400,
            }

        print("*** lambda_handler: Facebook signature ok")

    # Either a verified Facebook request or a verified EventBridge request
    print("*** lambda_handler: invoking Handler Lambda")
    lambda_client = boto3.client("lambda")
    response = lambda_client.invoke(
        FunctionName="aiChooseYourOwnAdventureHandler",
        InvocationType="Event",  # 'Event' for asynchronous invocation, 'RequestResponse' for synchronous
        Payload=json.dumps(event),
    )
    print("*** lambda_handler: invoking Handler Lambda complete: response", response)
    return {
        "statusCode": 200,
    }
