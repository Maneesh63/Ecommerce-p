from common.views import SignupView,LoginView,CurrentUserView
from django.urls import path
urlpatterns=[

    path('signup/',SignupView.as_view(),name='signup'),
    path('login/',LoginView.as_view(),name='login'),
    path('currentuser/<uuid:user_id>/',CurrentUserView.as_view(),name='currentuser')
]