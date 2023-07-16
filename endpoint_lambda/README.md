# AI Choose Your Own Adventure - Endpoint

### Receives scheduled requests from Event Bridge to create the story.
### Receives webhook events from Facebook when comments are added, to continue the story.
### Both are offloaded by asynchronously invoking the Handler Lambda.