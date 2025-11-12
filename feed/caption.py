def caption_image(image_path, prompt=None):
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
                {"type": "input_text", "text": "what's in this image?" if not prompt else prompt},
                {
                    "type": "input_image",
                    "file_id": file_id,
                },
            ],
        }],
    )
    from enhance.caption import detect_ai_error
    if detect_ai_error(response.output_text):
        from enahnce.caption_old import caption_image
        caption_image(image_path)
    return str(response.output_text)

def get_cv2_image_from_url(image_url):
    import cv2
    import urllib.request
    import numpy as np

    # Open the URL and read the image data
    with urllib.request.urlopen(image_url) as resp:
        image_data = resp.read()

    # Convert the image data to a NumPy array
    arr = np.asarray(bytearray(image_data), dtype=np.uint8)

    # Decode the image using cv2.imdecode
    # -1 means load the image as is (including alpha channel if present)
    return cv2.imdecode(arr, -1)

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
    from enhance.caption import detect_ai_error
    if detect_ai_error(response.output_text):
        from enahnce.caption_old import caption_image_cv2
        caption_image_cv2(get_cv2_image_from_url(image_url))
    return str(response.output_text)
