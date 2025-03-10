import zoneinfo
from django.utils import timezone

class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            # Get django_timezone from cookie
            tzname = request.COOKIES.get("django_timezone")
            if tzname:
                timezone.activate(zoneinfo.ZoneInfo(tzname)) # Activate
            else:
                timezone.deactivate()
        except Exception as e:
            timezone.deactivate()
            print(f'Timezone Exception: {e}')

        return self.get_response(request)