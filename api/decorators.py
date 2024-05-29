''' decorators for view functions '''

import json
from http import HTTPStatus

from django.db import models
from django.http import JsonResponse

from .models import Paper


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
            if request.method not in allowed_methods:
                return JsonResponse({'status': 'error', 'error': 'Method Not Allowed'}, status=HTTPStatus.METHOD_NOT_ALLOWED)
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
                return JsonResponse({'status': 'error', 'error': 'Unauthorized action, login required'}, status=HTTPStatus.UNAUTHORIZED)
            return func(request)
        return wrapper
    return decor


def paperid_exist():
    def decor(func):
        def wrapper(request):
            paperid = json.loads(request.body)['paperid']
            try:
                request.paper = Paper.objects.get(pk=paperid)
            except models.ObjectDoesNotExist:
                return JsonResponse({'status': 'error', 'error': f'paper of id {paperid} does not exist'}, status=HTTPStatus.BAD_REQUEST)
            return func(request)
        return wrapper
    return decor


def user_can_modify_paper():
    def decor(func):
        def wrapper(request):
            if request.user != request.paper.user:
                return JsonResponse({'status': 'error', 'error': 'user not authorized for this action'}, status=HTTPStatus.UNAUTHORIZED)
            return func(request)
        return wrapper
    return decor


def has_query_params(params: list[str]):
    '''
    GET request must have certain query params
    '''
    def decor(func):
        def wrapper(request):
            for i in params:
                if request.GET.get(i) is None:
                    return JsonResponse({'status': 'error', 'error': f'failed to get params: {i}'}, status=HTTPStatus.BAD_REQUEST)
            request.params = request.GET
            return func(request)
        return wrapper
    return decor
