import os
import requests
from django.contrib.auth.decorators import login_required
from django.http.response import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from context.models import e_Context as Context
from organization.models import Membership
from .authorization import context_organization_edit_permission_check
from notifications.signals import notify

# Renders the page that shows the progress of the mesh generation


@login_required
def mesh_status(request, contextCode):
    organizationCode = request.session['organizationCode']
    context = get_object_or_404(Context, organization__code=organizationCode, code=contextCode)
    # Authorization
    if not context_organization_edit_permission_check(request.user, context.organization):
        return HttpResponse('Unauthorized', status=401)

    return render(request, 'context/context/mesh_progress.html', {'context': context})

# Return last line of output


def get_last_line(status: str):
    if status == "":
        return ""
    lines: list = status.splitlines()
    if lines[-1] == "" or lines[-1].isspace():
        return get_last_line("\n".join(lines[0:len(lines)-1]))
    return lines[-1]


def get_status(last_line: str):
    error_substrings = [
        "Permission denied",
        "Fail"
        "Error",
        "/bin/sh: ./mesh: cannot execute binary file"
    ]
    finish_substrings = [
        "all files written in",
        "--:--:--"
    ]
    if any(s in last_line for s in error_substrings):
        return "Fail"
    elif any(s in last_line for s in finish_substrings):
        return "Finished successfully"
    else:
        return "Processing"


@login_required
def mesh_status_progress(request, contextCode):
    '''Function called by the frontend as an API endpoint to get the progress of the mesh generation'''
    organizationCode = request.session['organizationCode']
    context = get_object_or_404(Context, organization__code=organizationCode, code=contextCode)
    membership = Membership.objects.filter(organization=context.organization, user=request.user)
    if membership.count() == 0:
        return HttpResponse(status=401)

    log_file = os.path.join('logs', context.tag, 'mesh_log.txt')
    if not os.path.isfile(log_file):
        return HttpResponse(status=404)

    msg = ""
    with open(log_file, "r") as f_log:
        msg = f_log.read()
    lastline = get_last_line(msg)
    status = get_status(lastline)

    # Notification
    if ("Fail" in status) or ("Finished successfully" in status):
        notify.send(sender=context, recipient=context.requester, action_object=context.organization,
                    verb=f"Context {context.Name} has finished its processing with status '{status}'")

    return JsonResponse({'status': status, 'message': lastline, 'full_log': msg})

# API endpoint called by HiSTAV to notify that mesh generation has finished
# Expected to be called like: baseUrl/mesh-status/<str:contextCode>/change?organization=<str:organizationCode>&status=<status>


def mesh_status_change(request, contextCode):
    # since the request comes from HiSTAV, they have to send the organization as query param
    organizationCode = request.GET.get('organization')
    context = get_object_or_404(Context, organization__code=organizationCode, code=contextCode)
    if request.GET.get('status'):
        context.hasMesh = True
        context.task_id = None
    else:
        context.hasMesh = False

    context.save()

    return HttpResponse(status=200)

# Renders the confirm regeneration of mesh page


@login_required
def regenerate_mesh_confirm(request, contextCode):
    organizationCode = request.session['organizationCode']
    context = get_object_or_404(Context, organization__code=organizationCode, code=contextCode)
    # Authorization
    if not context_organization_edit_permission_check(request.user, context.organization):
        return HttpResponse('Unauthorized', status=401)

    return render(request, 'context/context/regenerate_mesh_confirm.html', {'context': context})

# Called repeatedly by the frontend when in /context/<str:contextCode>/detail to check if the mesh has been generated


@login_required
def inform_mesh_status(request, contextCode):
    organizationCode = request.session['organizationCode']
    context = get_object_or_404(Context, organization__code=organizationCode, code=contextCode)
    if context.hasMesh:
        return HttpResponse(status=200)
    else:
        return HttpResponse(status=400)
