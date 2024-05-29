''' register urls '''

from django.urls import path

from .views import post_delete_paper, post_insert_paper
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
]
