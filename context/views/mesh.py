import os
from django.contrib.auth.decorators import login_required
from django.http.response import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from context.models import e_Context as Context
from organization.models import Membership
from .authorization import context_organization_edit_permission_check
from notifications.signals import notify
from enum import Enum


class Status(Enum):
    FINISH = "Finished successfully"
    FAIL = "Fail"
    PROCESSING = "Processing"


@login_required
def mesh_status(request, contextCode):
    '''Renders the page that shows the progress of the mesh generation'''
    organizationCode = request.session['organizationCode']
    context = get_object_or_404(Context, organization__code=organizationCode, code=contextCode)
    # Authorization
    if not context_organization_edit_permission_check(request.user, context.organization):
        return HttpResponse('Unauthorized', status=401)

    return render(request, 'context/context/mesh_progress.html', {'context': context})


def get_last_line(status: str):
    '''Return last line of output'''
    if status == "":
        return ""
    lines: list = status.splitlines()
    if lines[-1] == "" or lines[-1].isspace():
        return get_last_line("\n".join(lines[0:len(lines)-1]))
    return lines[-1]


def tail(f, lines=1, _buffer=4098):
    """Tail a file and get X lines from the end"""
    """Source: https://stackoverflow.com/a/13790289/9847548"""
    # place holder for the lines found
    lines_found = []

    # block counter will be multiplied by buffer
    # to get the block size from the end
    block_counter = -1

    # loop until we find X lines
    while len(lines_found) < lines:
        try:
            f.seek(block_counter * _buffer, os.SEEK_END)
        except IOError:  # either file is too small, or too many lines requested
            f.seek(0)
            lines_found = f.readlines()
            break

        lines_found = f.readlines()

        # decrement the block counter to get the
        # next X bytes
        block_counter -= 1

    return lines_found[-lines:]


def get_status(last_line: str):
    error_substrings = [
        "Permission denied",
        "Fail"
        "Error",
        "/bin/sh: ./mesh: cannot execute binary file"
    ]
    finish_substrings = [
        "All files written in",
        "--:--:--",
        "Simulation finished successfully"
    ]
    if any(s in last_line for s in error_substrings):
        return Status.FAIL
    elif any(s in last_line for s in finish_substrings):
        return Status.FINISH
    else:
        return Status.PROCESSING


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
    if status == Status.FINISH:
        context.hasMesh = True
        context.task_id = None
        context.save()

        notify.send(sender=context, recipient=context.requester, action_object=context.organization,
                    verb=f"Processing of context {context.Name} has finished successfully")
    elif status == Status.FAIL:
        notify.send(sender=context, recipient=context.requester, action_object=context.organization,
                    verb=f"Processing of context {context.Name} has failed")

    return JsonResponse({'status': status.value, 'message': lastline, 'full_log': msg})


@login_required
def regenerate_mesh_confirm(request, contextCode):
    '''Renders the confirm regeneration of mesh page'''
    organizationCode = request.session['organizationCode']
    context = get_object_or_404(Context, organization__code=organizationCode, code=contextCode)
    # Authorization
    if not context_organization_edit_permission_check(request.user, context.organization):
        return HttpResponse('Unauthorized', status=401)

    return render(request, 'context/context/regenerate_mesh_confirm.html', {'context': context})


@login_required
def inform_mesh_status(request, contextCode):
    '''Called repeatedly by the frontend when in /context/<str:contextCode>/detail to check if the mesh has been generated'''
    organizationCode = request.session['organizationCode']
    context = get_object_or_404(Context, organization__code=organizationCode, code=contextCode)
    if context.hasMesh:
        return HttpResponse(status=200)
    else:
        return HttpResponse(status=400)
