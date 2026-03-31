import google.genai as genai


def call_gemini(prompt: str, api_key: str, stream: bool = True) -> str:
    client = genai.Client(api_key=api_key)

    if stream:
        print("\n" + "="*60)
        print("  GEMINI 2.5 FLASH — Generating Explanation...")
        print("="*60 + "\n")
        full_text = ""
        for chunk in client.models.generate_content_stream(
            model="gemini-2.5-flash",
            contents=prompt,
        ):
            if chunk.text:
                print(chunk.text, end="", flush=True)
                full_text += chunk.text
        print("\n")
        return full_text
    else:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        return response.text
