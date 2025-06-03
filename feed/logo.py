from django.conf import settings

def hex_to_bgr(hex_color):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (4, 2, 0))

def add_logo(path, author):
    import cv2
    if not author.vendor_profile.video_intro_font:
        img = cv2.imread(path)
        cv2.putText(img=img, text=author.vendor_profile.video_intro_text, org=(50 * int(2 * (img.shape[1]/2000)), 50 * int(3 * (img.shape[1]/2000))), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=int(2 * (img.shape[1]/2000)), color=(255, 255, 255), thickness=4 * int(2 * (img.shape[1]/2000)))
        cv2.imwrite(path, img)
        return path
    from PIL import ImageFont, ImageDraw, Image
    pil_image = Image.open(path)
    draw = ImageDraw.Draw(pil_image)
    font = ImageFont.truetype(author.vendor_profile.video_intro_font.path, size=int(2 * (img.shape[1]/2000)))
    draw.text((50 * int(2 * (img.shape[1]/2000)), 50 * int(3 * (img.shape[1]/2000))), author.vendor_profile.video_intro_text if author.vendor_profile.video_intro_text else settings.SITE_NAME, font=font, fill=hex_to_bgr(author.vendor_profile.video_intro_color))
    pil_image.save(path)
    return path
