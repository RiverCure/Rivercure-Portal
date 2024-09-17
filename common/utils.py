from re import compile, IGNORECASE
from PIL import Image

def is_mobile(request):
    """
    Return True if request is coming from a mobile device
    """
    MOBILE_AGENT_RE = compile(r".*(iphone|mobile|androidtouch)", IGNORECASE)
    
    if MOBILE_AGENT_RE.match(request.META['HTTP_USER_AGENT']):
        return True
    return False


def resize_image(image, height, width):
    """
    Resize image to given width and height and save
    """
    file_path = image.path
    output_size = (height,width)

    img = Image.open(file_path)
    if img.height > height or img.width > width:
        img.thumbnail(output_size)
        img.save(file_path)