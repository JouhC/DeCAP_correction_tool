from io import BytesIO
from PIL import Image
import base64
import logging

# Create a logger specific to this module
logger = logging.getLogger(__name__)

def decode_image(image_data):
    try:
        if isinstance(image_data, bytes):
            return Image.open(BytesIO(image_data))
        else:
            decoded = base64.b64decode(image_data)
            return Image.open(BytesIO(decoded))
    except:
        return None
    
def only_decode(image_data):
    """
    This function is used to decode an image from base64 or bytes.
    It returns None if the decoding fails.
    """
    try:
        return base64.b64decode(image_data)
    except Exception as e:
        logger.error(f"Error decoding image: {e}")
        return None