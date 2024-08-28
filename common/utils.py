from re import compile, IGNORECASE

def is_mobile(request):
    """
    Return True if request is coming from a mobile device
    """
    MOBILE_AGENT_RE = compile(r".*(iphone|mobile|androidtouch)", IGNORECASE)
    
    if MOBILE_AGENT_RE.match(request.META['HTTP_USER_AGENT']):
        return True
    return False