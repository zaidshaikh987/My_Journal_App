from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from . import views

urlpatterns = [
    # Core pages
    path("", views.index, name="index"),
    
    # Authentication
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register, name="register"),
    path("change-password/", views.change_password, name="change_password"),
    
    # Journal entries
    path("entries/", views.all_entries, name="all_entries"),
    path("entry/create/<str:date_str>/", views.create_entry, name="create_entry"),
    path("entry/edit/<int:entry_id>/", views.update_entry, name="update_entry"),
    path("entry/delete/<int:entry_id>/", views.delete_entry, name="delete_entry"),
    path("entry/date/<str:date>/", views.entry_on, name="entry_on"),
    
    # User profile
    path("profile/", views.profile, name="profile"),
    
    # Password reset
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset.html',
        email_template_name='registration/password_reset_email.html',
        subject_template_name='registration/password_reset_subject.txt'
    ), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html'
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html'
    ), name='password_reset_complete'),
    
    # API endpoints
    path("api/entries/", views.entries, name="entries"),
    path("api/entry/<int:entry_id>/", views.entry, name="entry"),
]
