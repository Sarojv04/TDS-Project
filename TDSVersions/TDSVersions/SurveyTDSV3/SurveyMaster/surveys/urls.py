from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

# Namespace for the app
app_name = 'surveys'

urlpatterns = [
    # Home Page
    path('', views.homepage, name='homepage'),  # Home page

    # Authentication Pages
    path('register/', views.register, name='register'),  # Register page
    path('login/', views.login, name='login'),  # Login page
    path('logout/', views.logout_view, name='logout'),  # Logout functionality

    # Role-Based Dashboards
    path('creator_dashboard/', views.creator_dashboard, name='creator_dashboard'),  # Creator dashboard
    path('taker_dashboard/', views.taker_dashboard, name='taker_dashboard'),  # Taker dashboard

    # Survey Management for Creators
    path('create_survey/', views.create_survey, name='create_survey'),  # Create a new survey
    path('edit_survey/<int:survey_id>/', views.edit_survey, name='edit_survey'),  # Edit an existing survey
    path('survey_results/<int:survey_id>/', views.survey_results, name='survey_results'),  # View survey results
    path('publish_survey/<int:survey_id>/', views.publish_survey, name='publish_survey'),  # Publish a survey
    path('close_survey/<int:survey_id>/', views.close_survey, name='close_survey'),  # Close a survey

    # Survey Taker Actions
    path('survey_list/', views.survey_list, name='survey_list'),  # List available surveys
    path('take_survey/<int:survey_id>/', views.take_survey, name='take_survey'),  # Take a survey
    path('submit_survey/<int:survey_id>/', views.submit_survey, name='submit_survey'),  # Submit survey response
    path('completion_message/', views.completion_message, name='completion_message'),  # Survey completion message

    # Password Reset Pages
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),  # Request password reset
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),  # Reset email sent
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),  # Link to reset
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),  # Reset successful

    # Debugging or Development Endpoint
    path('debug/<str:action>/', views.homepage, name='debug'),  # Placeholder for debugging or utility actions
]
