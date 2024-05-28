''' decorators for view functions '''

import json
from http import HTTPStatus

from django.http import JsonResponse


def has_json_payload():
    '''
    POST requests must have json payload
    '''
    def decor(func):
        def wrapper(request):
            if request.content_type != 'application/json':
                return JsonResponse({'status': 'error', 'error': 'content_type must be application/json'}, status=HTTPStatus.BAD_REQUEST)
            try:
                request.json_payload = json.loads(request.body)
            except json.JSONDecodeError as err:
                return JsonResponse({'status': 'error', 'error': f"payload can't be properly decoded: {err}"}, status=HTTPStatus.BAD_REQUEST)
            return func(request)
        return wrapper
    return decor



def allow_methods(allowed_methods: list[str]):
    '''
    the decorated function must be called with certain http methods
    '''
    def decor(func):
        def wrapper(request):
            print(type(request))
            if request.method not in allowed_methods:
                return JsonResponse({'error': 'Method Not Allowed'}, status=HTTPStatus.METHOD_NOT_ALLOWED)
            return func(request)
        return wrapper
    return decor


def login_required():
    '''
    decorated function must be called after user is authenticated
    '''
    def decor(func):
        def wrapper(request):
            if not request.user.is_authenticated:
                # or not request.user.is_permitted:
                return JsonResponse({'error': 'Unauthorized action, login required'}, status=HTTPStatus.UNAUTHORIZED)
            return func(request)
        return wrapper
    return decor
