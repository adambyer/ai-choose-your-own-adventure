from src.handlers import handle_get_request, handle_post_request


def lambda_handler(event, context):
    """Handle incoming requests from FB (webhook events) or AWS EventBridge (scheduled events)."""
    print("*** event", event)

    # Handle GET requests
    response_for_get = handle_get_request(event)
    if response_for_get:
        return response_for_get

    # Otherwise handle POST requests
    handle_post_request(event)

    return {
        'statusCode': 200,
    }
