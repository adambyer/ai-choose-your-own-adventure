# AI Choose Your Own Adventure

## Powered by AI, run on AWS Lambda, delivered on a Facebook page.

### Endpoint Lambda:
- Receives requests from EventBridge (scheduled) to post the beginning of the story.
- Receives webhook requests from Facebook when users comment on the story post with their choice.
- Both of these simply offload processing to the Handler Lambda and return.

### Handler Lambda:
- Receives events from the Endpoint Lambda to generate the story content and post it to Facebook.