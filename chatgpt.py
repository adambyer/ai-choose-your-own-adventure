import openai
import os

OPENAI_KEY = os.getenv("OPENAI_KEY")


def get_story(move):
    print("*** get_story")
    prompt = """
    Start a story in the style of "choose your own adventure".
    Prompt me with a numbered list of options for me to choose what happens next.
    """
    openai.api_key = OPENAI_KEY
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are an AI trained to write stories.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=1,
        max_tokens=500,
    )
    print("*** calling openai complete")

    # TODO: confirm finish_reason in response
    try:
        content = response["choices"][0]["message"]["content"]
    except Exception:
        print("*** error extracting message from response", response)

    return content
