import base64
from http import HTTPStatus
from hashlib import md5

from django.core.paginator import Paginator
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import QuerySet, Q
from django.http import JsonResponse

from .models import Paper, PaperByScholar
from .decorators import allow_methods, login_required, has_json_payload, \
        paperid_exist, user_can_modify_paper, has_query_params


def paginate_queryset(queryset: QuerySet, per_page: int, page: int = 1):
    # Paginate the queryset
    paginator = Paginator(queryset, per_page)
    page_obj = paginator.get_page(page)
    # Access the objects for the current page
    return page_obj.object_list


def save_paper(request):
    form: dict = request.json_payload
    form['user'] = request.user
    file_binary = base64.b64decode(form['file_content'])
    form['file_content'] = ContentFile(
            content=file_binary,
            name=md5(file_binary).hexdigest())
    # extract authors
    authors: list[str] = form.pop('authors')
    # TODO: make these atomic
    paper = Paper(**form)
    paper.save()
    print(f'paper {form["title"]} is made (but not saved yet)')
    return paper, authors


# Create your views here.
@allow_methods(['POST'])
@login_required()
@has_json_payload()
def post_insert_paper(request):
    ''' create scholar if not exist '''
    title = request.json_payload['title']
    if len(Paper.objects.filter(title=title)) != 0:
        return JsonResponse({'status': 'error', 'error': f'paper of title {title} already exists'}, status=HTTPStatus.BAD_REQUEST)
    try:
        with transaction.atomic():
            paper, authors = save_paper(request)
            for i in authors:
                PaperByScholar.objects.create(paper=paper, scholar=i)
                print(f'scholar {i} is inserted')
    except Exception as err:
        return JsonResponse({'status': 'error', 'error': f'exception occured: {err}'}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
    return JsonResponse({'status': 'Paper saved'})


# Create your views here.
@allow_methods(['POST'])
@login_required()
@has_json_payload()
@paperid_exist()
@user_can_modify_paper()
def post_delete_paper(request):
    ''' create scholar if not exist '''
    request.paper.delete()
    return JsonResponse({'status': 'Paper deleted'})


@allow_methods(['GET'])
@has_query_params(['title', 'per_page', 'page'])
@login_required()
def get_search_paper(request):
    ''' search by title/uploader/author/journal '''
    params = request.GET
    try:
        per_page = int(params['per_page'])
        page = int(params['page'])
    except KeyError:
        return JsonResponse({'error': 'per_page and page should be integer number'}, status=HTTPStatus.BAD_REQUEST)
    queryset = Paper.objects.filter(title__regex=params.get('title'))
    if params.get('journal'):
        queryset = queryset.filter(journal=params.get('journal'))
    if params.get('uploader'):
        queryset = queryset.filter(user__username__regex=params.get('uploader'))
    if params.get('author'):
        queryset = queryset.filter(paperbyscholar__scholar__regex=params.get('author'))
    # then filter private
    # test this some day
    queryset = queryset.filter(Q(private=False) | Q(user=request.user))
    return JsonResponse({'status': 'ok', 'data': [i.json for i in paginate_queryset(queryset, per_page, page)]})
