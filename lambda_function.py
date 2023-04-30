from handlers import handle_get, handle_post


def lambda_handler(event, context):
    print("*** event", event)

    # Handle GET requests
    response_for_get = handle_get(event)
    if response_for_get:
        return response_for_get

    # Otherwise handle POST requests
    response_for_post = handle_post(event)
    if response_for_post:
        return response_for_post

    return {
        'statusCode': 200,
        "request": event,
    }
