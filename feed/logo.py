from django.conf import settings

def hex_to_rgb(hex_color):
  """
  Converts a hexadecimal color string (e.g., "#RRGGBB" or "RRGGBB") to an RGB tuple.
  """
  hex_color = hex_color.lstrip('#')  # Remove '#' if present
  if len(hex_color) != 6:
    raise ValueError("Invalid hex color format. Expected 'RRGGBB'.")
  r = int(hex_color[0:2], 16)
  g = int(hex_color[2:4], 16)
  b = int(hex_color[4:6], 16)
  return (r, g, b)

def add_logo(path, output_path, author):
    print('Adding logo')
    import cv2
    img = cv2.imread(path)
    if not author.vendor_profile.video_intro_font:
        cv2.putText(img=img, text=author.vendor_profile.video_intro_text, org=(50 * int(2 * (img.shape[1]/2000)), 50 * int(3 * (img.shape[1]/2000))), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=int(2 * (img.shape[1]/2000)), color=(255, 255, 255), thickness=4 * int(2 * (img.shape[1]/2000)))
        cv2.imwrite(output_path, img)
        return output_path
    from PIL import ImageFont, ImageDraw, Image
    pil_image = Image.open(path)
    draw = ImageDraw.Draw(pil_image)
    print('Font size {}'.format(str(int(90 * (img.shape[1]/2000)))))
    font = ImageFont.truetype(author.vendor_profile.video_intro_font.path, size=int(90 * (img.shape[1]/2000)))
    draw.text((int(50*2 * (img.shape[1]/2000)), int(50*2 * (img.shape[1]/2000))), author.vendor_profile.video_intro_text if author.vendor_profile.video_intro_text else settings.SITE_NAME, font=font, fill=hex_to_rgb(author.vendor_profile.video_intro_color))
    pil_image.save(output_path)
    print(output_path)
    return output_path
