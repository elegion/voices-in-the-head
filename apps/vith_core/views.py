from django.http import HttpResponse

from core import JsonResponse
from vith_core.forms import UploadForm


def tracks(request):
    """
    Return list of all uploaded tracks in json format
    """
    
    return HttpResponse('test')


def upload(request):
    """
    Uploads and enqueues track
    """
    form = UploadForm(request.POST, request.FILES)
    if form.is_valid():
        track = form.save(commit=False)
        track.length = 0
        track.save()
        return JsonResponse({
            'status': 'ok',
            'name': track.name,
            'length': track.length
        })
    
    return JsonResponse({
        'status': 'error',
        'errors': dict(form.errors)
    });