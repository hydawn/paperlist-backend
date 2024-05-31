''' decorators for view functions '''

import json
from http import HTTPStatus

from django.db import models
from django.http import JsonResponse

from .models import Paper, PaperSet


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


def paperid_exist(method: str):
    def decor(func):
        def wrapper(request):
            if method in ['post', 'POST']:
                paperid = json.loads(request.body)['paperid']
            else:
                # make it int?
                try:
                    paperid = int(request.GET.get('paperid'))
                except ValueError:
                    return JsonResponse({'status': 'error', 'error': 'paperid should be integer'}, status=HTTPStatus.BAD_REQUEST)
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


def user_can_comment_paper():
    def decor(func):
        def wrapper(request):
            if request.user != request.paper.user and request.paper.private:
                return JsonResponse({'status': 'error', 'error': 'user not authorized to comment'}, status=HTTPStatus.UNAUTHORIZED)
            return func(request)
        return wrapper
    return decor


def user_can_view_paper():
    def decor(func):
        def wrapper(request):
            if request.user == request.paper.user:
                return func(request)
            if request.paper.private:
                return JsonResponse({'status': 'error', 'error': 'user not authorized to view'}, status=HTTPStatus.UNAUTHORIZED)
            return func(request)
        return wrapper
    return decor


def paperset_exists(method: str):
    def decor(func):
        def wrapper(request):
            if method in ['post', 'POST']:
                papersetid = json.loads(request.body)['papersetid']
            elif method in ['get', 'GET']:
                # make it int?
                try:
                    papersetid = int(request.GET.get('papersetid'))
                except ValueError:
                    return JsonResponse({'status': 'error', 'error': 'papersetid should be integer'}, status=HTTPStatus.BAD_REQUEST)
            else:
                return  JsonResponse({'status': 'error', 'error': 'internal error'}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            try:
                request.paperset = PaperSet.objects.get(pk=papersetid)
            except models.ObjectDoesNotExist:
                return JsonResponse({'status': 'error', 'error': f'paperset of id {papersetid} does not exist'}, status=HTTPStatus.BAD_REQUEST)
            return func(request)
        return wrapper
    return decor


def user_paperset_action(action: str):
    def decor(func):
        def wrapper(request):
            if action in ['read', 'comment']:
                # the owner has the permission to read
                if request.user == request.paperset.user:
                    return func(request)
                # others have no permission to read if it's private
                if request.paperset.private:
                    return JsonResponse({'status': 'error', 'error': 'user not authorized to read'}, status=HTTPStatus.UNAUTHORIZED)
                return func(request)
            if action == 'write':
                # only the owner has the permission to write
                if request.user == request.paperset.user:
                    return func(request)
                return JsonResponse({'status': 'error', 'error': 'user not authorized to write'}, status=HTTPStatus.UNAUTHORIZED)
            return JsonResponse({'status': 'error', 'error': 'internal error'}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
        return wrapper
    return decor


def paperid_list_exist(method: str):
    def decor(func):
        def wrapper(request):
            if method not in ['post', 'POST']:
                return JsonResponse({'status': 'error', 'error': 'internal error'}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            try:
                paperid_list = [int(i) for i in json.loads(request.body)['paperid_list']]
                request.paper_list = Paper.objects.filter(id__in=paperid_list)
            except models.ObjectDoesNotExist as err:
                return JsonResponse({'status': 'error', 'error': f'paper list does not exist: {err}'}, status=HTTPStatus.BAD_REQUEST)
            except ValueError:
                return JsonResponse({'status': 'error', 'error': 'paperid should be integers'}, status=HTTPStatus.BAD_REQUEST)
            return func(request)
        return wrapper
    return decor
