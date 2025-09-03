def generate_event_qrcode(event):
    import os
    from django.conf import settings
    from events.models import get_event_path
    path = get_event_path(None, 'event.png')
    generate_qrcode(event.meeting.get_absolute_url(), os.path.join(settings.BASE_DIR, 'media/', path))
    event.image = path
    event.save()

def generate_qrcode(data, out_path):
    import qrcode

    # Create a QRCode object with border settings
    # 'border' parameter controls the size of the quiet zone (border) around the QR code.
    # The default value is 4 modules.
    qr = qrcode.QRCode(
        version=1,  # Version of the QR code (1 to 40). None for automatic sizing.
        error_correction=qrcode.constants.ERROR_CORRECT_L, # Error correction level
        box_size=10, # Size of each box (pixel) in the QR code
        border=6, # Border size in modules (e.g., 6 for a wider border)
    )

    # Add data to the QR code
    qr.add_data(data)
    qr.make(fit=True) # Ensure the QR code fits within the version and border settings

    # Create an image from the QR code and save it
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(out_path)
    return out_path
