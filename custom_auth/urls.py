from django.urls import path
from . import views

app_name = "auth"

urlpatterns = [
    path('', views.MainPage.as_view(), name='main'),
    path('auth/login', views.LoginView.as_view(), name='login'),
    path('auth/signup/', views.SignUpView.as_view(), name='signup'),
    path('auth/confirm_email/<str:uid>/<str:token>/', views.ConfirmEmailView.as_view(), name='confirm_email'),
    path('auth/password_reset/', views.PasswordResetRequestView.as_view(), name='password_reset'),
    path('auth/reset/<int:uid>/<str:token>/', views.PasswordResetConfirmView.as_view(), name='reset_password_confirm'),
    path('auth/logout', views.LogoutView.as_view(), name='logout')
]
