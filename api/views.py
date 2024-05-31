import base64
from http import HTTPStatus
from hashlib import md5

from django.contrib.auth.models import User
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import QuerySet, Q, Avg
from django.http import HttpResponse, JsonResponse

from .models import Paper, PaperByScholar, PaperSet, PaperTextComments, \
        PaperStarComments, PaperSetContent
from .decorators import allow_methods, login_required, has_json_payload, \
        paperid_exist, paperid_list_exist, paperset_exists, user_can_modify_paper, has_query_params, \
        user_can_comment_paper, user_can_view_paper, user_paperset_action


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


def search_paper(params: dict[str, str], user: User) -> QuerySet:
    use_regex: bool = params.get('regex', 'False') in ['true', 'True']
    papersetid = params.get('papersetid')
    if papersetid:
        paperset_set = PaperSet.objects.filter(pk=int(papersetid))
        if len(paperset_set) != 0:
            queryset = Paper.objects.filter(id__in=paperset_set[0].has_paper.all().values_list('paper_id', flat=True))
        else:
            queryset = Paper.objects.all()
    else:
        queryset = Paper.objects.all()
    if params.get('title'):
        if use_regex:
            queryset = queryset.filter(title__regex=params.get('title'))
        elif params.get('title') != '':
            queryset = queryset.filter(title__icontains=params.get('title'))
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
    return queryset.filter(Q(private=False) | Q(user=user))


def search_paperset_only(params: dict[str, str], user: User) -> QuerySet:
    use_regex = params.get('regex', 'False') in ['true', 'True']
    name = params.get('name')
    if not name:
        queryset = PaperSet.objects.all()
    elif use_regex:
        queryset = PaperSet.objects.filter(name__regex=name)
    else:
        queryset = PaperSet.objects.filter(name__icontains=name)
    description = params.get('description')
    if description:
        if use_regex:
            queryset = queryset.filter(description__regex=description)
        else:
            queryset = queryset.filter(description__icontains=description)
    creater = params.get('creater')
    if creater:
        if use_regex:
            queryset = queryset.filter(user__username__regex=creater)
        else:
            queryset = queryset.filter(user__username__icontains=creater)
    return queryset.filter(Q(private=False) | Q(user=user))


def search_paperset_bypaper(params: dict[str, str], user: User) -> QuerySet:
    search_paper_params = {}
    for i in ['papertitle', 'paperjournal', 'paperuploader', 'paperauthor']:
        if i in params:
            search_paper_params[i[len('paper'):]] = params[i]
    paper_queryset = search_paper(search_paper_params, user)
    paper_set_content = PaperSetContent.objects.filter(paper__in=paper_queryset)
    paper_set_ids = paper_set_content.values_list('paper_set', flat=True).distinct()
    return PaperSet.objects.filter(id__in=paper_set_ids).filter(Q(private=False) | Q(user=user))


def search_paperset(params: dict[str, str], user: User) -> QuerySet:
    for i in ['papertitle', 'paperjournal', 'paperuploader', 'paperauthor']:
        if i in params:
            return search_paperset_bypaper(params, user)
    return search_paperset_only(params, user)


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
@paperid_exist('POST')
@user_can_modify_paper()
def post_delete_paper(request):
    ''' create scholar if not exist '''
    request.paper.delete()
    return JsonResponse({'status': 'ok', 'message': 'paper deleted'})


@allow_methods(['GET'])
@login_required()
def get_search_paper(request):
    ''' search by title/uploader/author/journal '''
    params: dict = request.GET
    try:
        per_page = int(params.get('per_page', 3))
        page = int(params.get('page', 1))
    except ValueError:
        return JsonResponse({'error': 'per_page and page should be integer number'}, status=HTTPStatus.BAD_REQUEST)
    queryset = search_paper(params, request.user)
    page, total_page, current_page = paginate_queryset(queryset.order_by('id'), per_page, page)
    return JsonResponse({'status': 'ok', 'data': {
            'data_list': [i.simple_json for i in page],
            'total_page': total_page,
            'current_page': current_page,
        }})


@allow_methods(['POST'])
@login_required()
@has_json_payload()
@paperid_exist('POST')
@user_can_comment_paper()
def post_comment_paper(request):
    ''' create scholar if not exist '''
    try:
        comment = request.json_payload['comment']
    except KeyError:
        return JsonResponse({'error': 'comment does not exist!'}, status=HTTPStatus.BAD_REQUEST)
    PaperTextComments.objects.create(paper=request.paper, user=request.user, comment=comment)
    return JsonResponse({'status': 'ok'})


@allow_methods(['POST'])
@login_required()
@has_json_payload()
@paperid_exist('POST')
@user_can_comment_paper()
def post_review_paper(request):
    ''' make stars '''
    try:
        star = int(request.json_payload['star'])
    except KeyError:
        return JsonResponse({'error': 'star does not exist!'}, status=HTTPStatus.BAD_REQUEST)
    except ValueError:
        return JsonResponse({'error': 'star gotta be a number 1-5'}, status=HTTPStatus.BAD_REQUEST)
    queryset = PaperStarComments.objects.filter(paper=request.paper, user=request.user)
    if len(queryset) == 0:
        PaperStarComments.objects.create(paper=request.paper, user=request.user, star=star)
        return JsonResponse({'status': 'ok'})
    queryset[0].star = star
    queryset[0].save()
    return JsonResponse({'status': 'ok', 'message': 'review changed'})


@allow_methods(['GET'])
@login_required()
@has_query_params(['paperid', 'per_page', 'page'])
@paperid_exist('GET')
@user_can_view_paper()
def get_search_paper_comment(request):
    try:
        per_page = int(request.GET['per_page'])
        page = int(request.GET['page'])
    except ValueError:
        return JsonResponse({'error': 'per_page and page should be integer number'}, status=HTTPStatus.BAD_REQUEST)
    paper_comment = PaperTextComments.objects.filter(paper=request.paper).order_by('commented_on')
    paper_comment, total_page, current_page = paginate_queryset(paper_comment, per_page, page)
    return JsonResponse(
            {
                'status': 'ok',
                'data': {
                    'comment_list': [i.json for i in paper_comment],
                    'total_page': total_page,
                    'current_page': current_page,
                }
            })


@allow_methods(['GET'])
@login_required()
@has_query_params(['paperid'])
@paperid_exist('GET')
@user_can_view_paper()
def get_get_paper_review(request):
    # review is the avg of all
    review: float | None = PaperStarComments.objects.filter(paper=request.paper).aggregate(Avg('star'))['star__avg']
    return JsonResponse({'status': 'ok', 'data': { 'review':  0 if review is None else round(review, 1) }})


@allow_methods(['GET'])
@login_required()
@has_query_params(['paperid'])
@paperid_exist('GET')
@user_can_view_paper()
def get_paper_detail(request):
    detail_json = request.paper.simple_json
    return JsonResponse({'status': 'ok', 'data': detail_json})


@allow_methods(['GET'])
@login_required()
@has_query_params(['paperid'])
@paperid_exist('GET')
@user_can_view_paper()
def get_paper_content(request):
    if request.GET.get('type') == 'bytes':
        if request.GET.get('preview_page'):
            return HttpResponse(content=request.paper.file_bytes_preview(num_pages=int(request.GET.get('preview_page'))))
        return HttpResponse(content=request.paper.file_bytes)
    return JsonResponse({'status': 'ok', 'data': request.paper.full_json})


@allow_methods(['POST'])
@login_required()
@has_json_payload()
def post_insert_paperset(request):
    try:
        PaperSet.objects.create(user=request.user, **request.json_payload)
    except Exception:
        return JsonResponse({'error': 'paper set cannot be created'}, status=HTTPStatus.BAD_REQUEST)
    return JsonResponse({'status': 'ok', 'message': 'paperset created'})


@allow_methods(['POST'])
@login_required()
@has_json_payload()
@paperset_exists('POST')
@user_paperset_action('write')
def post_change_paperset(request):
    changed = False
    if request.json_payload.get('name'):
        request.paperset.name = request.json_payload.get('name')
        changed = True
    if request.json_payload.get('description'):
        request.paperset.description = request.json_payload.get('description')
        changed = True
    if 'private' in request.json_payload:
        request.paperset.private = request.json_payload['private']
        changed = True
    if not changed:
        return JsonResponse({'status': 'warning', 'warning': 'no changes were made'})
    request.paperset.save()
    return JsonResponse({'status': 'ok', 'message': 'paperset changed'})


@allow_methods(['GET'])
@login_required()
def get_search_paperset(request):
    '''
    now this is complicated, you can search papserset's name, description, user
    or search like search paper and then get that paper's paperset
    and in the end, don't forget the private
    '''
    params: dict = request.GET
    try:
        per_page = int(params.get('per_page', 3))
        page = int(params.get('page', 1))
    except ValueError:
        return JsonResponse({'error': 'per_page and page should be integer number'}, status=HTTPStatus.BAD_REQUEST)
    queryset = search_paperset(request.GET, request.user)
    page, total_page, current_page = paginate_queryset(queryset.order_by('id'), per_page, page)
    return JsonResponse({'status': 'ok', 'data': {
            'data_list': [i.json for i in page],
            'total_page': total_page,
            'current_page': current_page,
        }})


@allow_methods(['POST'])
@login_required()
@has_json_payload()
@paperid_list_exist('POST')
@paperset_exists('POST')
@user_paperset_action('write')
def post_add_to_paperset(request):
    already_in: list[Paper] = []
    for paper in request.paper_list:
        param = { 'paper': paper, 'paper_set': request.paperset }
        if len(PaperSetContent.objects.filter(**param)) != 0:
            already_in.append(paper)
        else:
            PaperSetContent.objects.create(**param)
    if len(already_in) == 0:
        return JsonResponse({'status': 'ok', 'message': 'all is added'})
    return JsonResponse(
            {
                'status': 'warning',
                'warning': 'some papers are already in paperset',
                'data': {
                    'already_in': [i.simple_json for i in already_in]
                    }
            })


@allow_methods(['POST'])
@login_required()
@has_json_payload()
@paperid_list_exist('POST')
@paperset_exists('POST')
@user_paperset_action('write')
def post_delete_from_paperset(request):
    for paper in request.paper_list:
        param = { 'paper': paper, 'paper_set': request.paperset }
        queryset = PaperSetContent.objects.filter(**param)
        if len(queryset) != 1:
            return JsonResponse({'status': 'error', 'error': 'paper not in paperset', 'data': { 'paper': paper.simple_json }}, status=HTTPStatus.BAD_REQUEST)
        queryset[0].delete()
    return JsonResponse({'status': 'ok', 'message': 'all is removed'})


@allow_methods(['GET'])
@login_required()
@paperset_exists('GET')
@user_paperset_action('read')
def get_get_paperset_papers(request):
    return JsonResponse({'status': 'ok', 'data': { 'paper_list': [i.paper.simple_json for i in request.paperset.has_paper.all()] }})
