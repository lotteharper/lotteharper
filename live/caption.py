def caption_thumbnail(image_path, prompt=None, title=None):
    from feed.caption import caption_image
    return caption_image(image_path, prompt='Write a detailed, comprehensive and thorough essay about this image including specific details about what is seen' + (' and include an interpretation of the title, "{}"'.format(title) if title else '') + ' and the prompt, \'{}\'. Include comprehensive details about the image and use a professional, friendly tone and language.'.format(prompt if prompt else 'What\'s in this image?'))
