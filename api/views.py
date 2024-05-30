import base64
from http import HTTPStatus
from hashlib import md5

from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import QuerySet, Q
from django.http import JsonResponse

from .models import Paper, PaperByScholar, PaperTextComments, PaperStarComments
from .decorators import allow_methods, login_required, has_json_payload, \
        paperid_exist, user_can_modify_paper, has_query_params, \
        user_can_comment_paper


def paginate_queryset(queryset: QuerySet, per_page: int, page: int = 1):
    # Paginate the queryset
    paginator = Paginator(queryset, per_page)
    try:
        page_list = paginator.page(page)
    except PageNotAnInteger:
        page_list = paginator.page(1)
    except EmptyPage:
        page_list = paginator.page(paginator.num_pages)
    # Access the objects for the current page
    return page_list, paginator.num_pages, page_list.number


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
    return JsonResponse({'status': 'ok', 'message': 'paper inserted'})


# Create your views here.
@allow_methods(['POST'])
@login_required()
@has_json_payload()
@paperid_exist()
@user_can_modify_paper()
def post_delete_paper(request):
    ''' create scholar if not exist '''
    request.paper.delete()
    return JsonResponse({'status': 'ok', 'message': 'paper deleted'})


@allow_methods(['GET'])
@has_query_params(['per_page', 'page'])
@login_required()
def get_search_paper(request):
    ''' search by title/uploader/author/journal '''
    params: dict = request.GET
    use_regex: bool = request.GET.get('regex', 'False') in ['true', 'True']
    try:
        per_page = int(params['per_page'])
        page = int(params['page'])
    except KeyError:
        return JsonResponse({'error': 'per_page and page should be integer number'}, status=HTTPStatus.BAD_REQUEST)
    if params.get('journal'):
        if use_regex:
            queryset = Paper.objects.filter(title__regex=params.get('title'))
        elif params.get('title') == '':
            queryset = Paper.objects.all()
        else:
            queryset = Paper.objects.filter(title__icontains=params.get('title'))
    else:
        queryset = Paper.objects.all()
    if params.get('journal'):
        if use_regex:
            queryset = queryset.filter(journal__regex=params.get('journal'))
        elif params.get('journal') != '':
            queryset = queryset.filter(journal__icontains=params.get('journal'))
    if params.get('uploader'):
        if use_regex:
            queryset = queryset.filter(user__username__regex=params.get('uploader'))
        elif params.get('uploader') != '':
            queryset = queryset.filter(user__username__icontains=params.get('uploader'))
    if params.get('author'):
        if use_regex:
            queryset = queryset.filter(paperbyscholar__scholar__regex=params.get('author'))
        elif params.get('author') != '':
            queryset = queryset.filter(paperbyscholar__scholar__icontains=params.get('author'))
    # then filter private
    # test this some day
    queryset = queryset.filter(Q(private=False) | Q(user=request.user))
    page, total_page, current_page = paginate_queryset(queryset.order_by('id'), per_page, page)
    return JsonResponse({'status': 'ok', 'data': {
            'data_list': [i.simple_json for i in page],
            'total_page': total_page,
            'current_page': current_page,
        }})


@allow_methods(['POST'])
@login_required()
@has_json_payload()
@paperid_exist()
@user_can_comment_paper()
def post_comment_paper(request):
    ''' create scholar if not exist '''
    PaperTextComments.objects.create(paper=request.paper, user=request.user, comment=request.json_payload.comment)
    return JsonResponse({'status': 'ok'})


@allow_methods(['POST'])
@login_required()
@has_json_payload()
@paperid_exist()
@user_can_comment_paper()
def post_review_paper(request):
    ''' make stars '''
    try:
        star = int(request.json_payload.star)
    except KeyError:
        return JsonResponse({'error': 'star gotta be a number 1-5'})
    PaperStarComments.objects.create(paper=request.paper, user=request.user, star=star)
    return JsonResponse({'status': 'ok'})
