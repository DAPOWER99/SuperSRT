import os
from openrouter import OpenRouter
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

with OpenRouter(api_key=os.getenv("OPENROUTER_API_KEY")) as client:
    
    # Send a chat request as a sample
    response = client.chat.send(
        model = "nvidia/nemotron-3-nano-30b-a3b:free",  # You can change this to any model slug (THIS IS A SAMPLE MODEL FOR TESTING)
        messages=[
            {
                "role": "user",
                "content": "Hello! Give me a fun fact about programming in a single sentence.",
            }
        ],
        stream=False
    )

    # 4. Print the result
    print("Response from OpenRouter:")
    print(response.choices[0].message.content)
