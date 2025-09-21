import base64
from PIL import Image
from io import BytesIO

def base64_to_image(base64_string):
    # Remove the data URI prefix if present
    if "data:image" in base64_string:
        base64_string = base64_string.split(",")[1]

    # Decode the Base64 string into bytes
    image_bytes = base64.b64decode(base64_string)
    return image_bytes

def create_image_from_bytes(image_bytes):
    # Create a BytesIO object to handle the image data
    image_stream = BytesIO(image_bytes)

    # Open the image using Pillow (PIL)
    image = Image.open(image_stream)
    return image

def create_qr_code_image(qr_code_base64):
    # Convert the Base64 string to image bytes
    image_bytes = base64_to_image(qr_code_base64)

    # Create an image from the bytes
    qr_code_image = create_image_from_bytes(image_bytes)
    return qr_code_image