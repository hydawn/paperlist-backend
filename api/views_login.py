''' view functions for login related actions '''

from http import HTTPStatus

from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User

from .decorators import has_json_payload, login_required, allow_methods


@allow_methods(['POST'])
@has_json_payload()
def post_login(request):
    try:
        username = request.json_payload.get('username')
        password = request.json_payload.get('password')
        if not (username and password):
            return JsonResponse({'error': f'Username [{username}] or Password [{password}] not provided or Empty'}, status=HTTPStatus.BAD_REQUEST)
    except KeyError:
        return JsonResponse({'status': 'error', 'error': 'username or password not found or empty'}, status=HTTPStatus.BAD_REQUEST)
    if request.user.is_authenticated:
        return JsonResponse({'status': 'ok', 'message': f'[{username}] already logged in'}, status=HTTPStatus.OK)
    user = authenticate(request, username=username, password=password)
    if user:
        login(request, user)
        ok_message = {'status': 'ok', 'message': 'login success'}
        return JsonResponse(ok_message)
    error_message = {'status': 'error', 'error': 'invalid credentials'}
    return JsonResponse(error_message, status=HTTPStatus.UNAUTHORIZED)


@allow_methods(['POST'])
@has_json_payload()
def post_signup(request):
    username = request.json_payload.get('username')
    password = request.json_payload.get('password')
    email = request.json_payload.get('email')
    if not (username and email and password):
        return JsonResponse({'error': 'Username, password and email are required'}, status=HTTPStatus.BAD_REQUEST)
    if User.objects.filter(username=username).exists():
        return JsonResponse({'error': 'Username already exists'}, status=HTTPStatus.BAD_REQUEST)
    User.objects.create_user(username=username, email=email, password=password)
    return JsonResponse({'message': 'User created successfully'}, status=HTTPStatus.CREATED)


@allow_methods(['GET'])
@login_required()
def get_user_detail(request):
    user = User.objects.get(username=request.user.username)
    return JsonResponse(
        {
            'username': user.username,
            'email': user.email,
            'last_login': user.last_login,
        })


@allow_methods(['GET'])
def get_user_loggedin(request):
    if request.user and request.user.is_authenticated:
        return JsonResponse({'status': 'ok', 'loggedin': True})
    return JsonResponse({'status': 'ok', 'loggedin': False})


@allow_methods(['POST'])
@login_required()
def post_logout(request):
    ''' log the user out '''
    logout(request)
    return JsonResponse({'status': 'ok'})


@allow_methods(['POST'])
@login_required()
def post_logoff(request):
    request.user.delete()
    return JsonResponse({'status': 'ok'})
