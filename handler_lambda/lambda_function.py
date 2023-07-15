from src.handlers import handle_request


def lambda_handler(event, context):
    """Handle incoming requests from the Endpoint Lambda."""
    print("*** lambda_handler", event)

    handle_request(event)

    return {
        'statusCode': 200,
    }
