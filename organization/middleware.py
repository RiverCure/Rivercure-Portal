from django.contrib import messages
from django.shortcuts import redirect
from django.urls import resolve

class CheckOrganizationInSession:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.
        if request.user.is_authenticated: # Authentication is handled by another middleware
            if request.path.startswith('/contexts/') or request.path.startswith('/sensors/'):
                # This is an exception for HiSTAV to be able to communicate
                if not resolve(request.path_info).url_name == 'mesh-status-change':
                    if not request.session.get('organizationCode', False):
                        messages.warning(request, 'Please first choose an organization')
                        return redirect('organization-list')

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response