def caption_image(image_path):
    from django.conf import settings
    from openai import OpenAI

    client = OpenAI(api_key=settings.OPENAI_KEY)

    # Function to create a file with the Files API
    def create_file(file_path):
      with open(file_path, "rb") as file_content:
        result = client.files.create(
            file=file_content,
            purpose="vision",
        )
        return result.id

    # Getting the file ID
    file_id = create_file(image_path)

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[{
            "role": "user",
            "content": [
                {"type": "input_text", "text": "what's in this image?"},
                {
                    "type": "input_image",
                    "file_id": file_id,
                },
            ],
        }],
    )
    return response.output_text

def caption_image_url(image_url):
    from django.conf import settings
    from openai import OpenAI

    client = OpenAI(api_key=settings.OPENAI_KEY)

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[{
            "role": "user",
            "content": [
                {"type": "input_text", "text": "what's in this image?"},
                {
                    "type": "input_image",
                    "image_url": image_url,
                },
            ],
        }],
    )
    return response.output_text
