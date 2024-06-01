''' register urls '''

from django.urls import path

from .views import get_search_paper, post_add_to_paperset, post_delete_paper, \
        post_insert_paper, get_paper_detail, get_paper_content, \
        post_insert_paperset, post_comment_paper, post_review_paper, \
        get_get_paper_review, get_search_paper_comment, get_search_paperset, \
        get_get_papers_paperset, post_delete_from_paperset, \
        post_change_paperset
from .views_login import post_login, post_logout, post_signup, get_user_detail, \
        get_user_loggedin

urlpatterns = [
    path('login', post_login),
    path('logout', post_logout),
    path('signup', post_signup),
    path('get_user_detail', get_user_detail),
    path('get_user_loggedin', get_user_loggedin),
    path('insert_paper', post_insert_paper),
    path('delete_paper', post_delete_paper),
    path('search_paper', get_search_paper),
    path('paper_detail', get_paper_detail),
    path('paper_content', get_paper_content),
    path('comment_paper', post_comment_paper),
    path('review_paper', post_review_paper),
    path('search_paper_comment', get_search_paper_comment),
    path('get_paper_review', get_get_paper_review),
    path('insert_paperset', post_insert_paperset),
    path('search_paperset', get_search_paperset),
    path('add_to_paperset', post_add_to_paperset),
    path('delete_from_paperset', post_delete_from_paperset),
    path('change_paperset', post_change_paperset),
    path('get_papers_paperset', get_get_papers_paperset),
]
