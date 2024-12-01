from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

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
    path('survey_results/<int:survey_id>/', views.survey_results, name='survey_results'),  # View Published Results
    path('submit_survey/<int:survey_id>/', views.submit_survey, name='submit_survey'),  # Submit survey response
    path('close_survey/<int:survey_id>/', views.close_survey, name='close_survey'),  # Close a survey

    # Survey Taker Pages
    path('survey_list/', views.survey_list, name='survey_list'),  # List available surveys
    path('take_survey/<int:survey_id>/', views.take_survey, name='take_survey'),  # Take a survey
    path('completion_message/', views.completion_message, name='completion_message'),  # Survey completion message

    # Additional Survey Actions
    path('save_survey_draft/', views.create_survey, name='save_survey_draft'),  # Save survey as draft
    path('publish_survey/<int:survey_id>/', views.publish_survey, name='publish_survey'),  # Publish a survey

    # Republished Surveys Functionality
    path('republish_survey/<int:survey_id>/', views.republish_survey, name='republish_survey'),  # Republish a survey
    path('take_republished_survey/<int:survey_id>/', views.take_republished_survey, name='take_republished_survey'),  # Take a republished survey
    path('aggregated_results/<int:survey_id>/', views.aggregated_results, name='aggregated_results'),  # View RePublished Results

    # Survey Response Table (Admin View of Survey Responses)
    path('survey_responses/<int:survey_id>/', views.survey_response_table, name='survey_response_table'),  # View survey responses table

    # Password Reset Pages
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),  # Request password reset
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),  # Reset email sent
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),  # Link to reset
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),  # Reset successful
    
    path('view_results/<int:survey_id>/', views.view_results, name='view_results'),

    # Debugging Endpoint (Optional, for Development)
    path('debug/', views.homepage, name='debug'),  # Temporary debugging route
]
