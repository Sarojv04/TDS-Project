from django.urls import path
from . import views  # Import views from the Survey app

urlpatterns = [
    path('', views.homepage, name='homepage'),  # Entry point for homepage
    path('register/', views.register, name='register'),  # Registration page
    path('login/', views.login_view, name='login'),  # Login page
    path('creator/dashboard/', views.creator_dashboard, name='creator_dashboard'),  # Creator Dashboard
    path('taker/dashboard/', views.taker_dashboard, name='taker_dashboard'),  # Taker Dashboard
    path('create_survey/', views.create_survey, name='create_survey'),  # Page for creating a new survey
    path('edit_survey/<int:survey_id>/', views.edit_survey, name='edit_survey'),  # Page to edit a survey
    path('manage_surveys/', views.manage_surveys, name='manage_surveys'),  # Page to manage existing surveys
    path('survey_list/', views.survey_list, name='survey_list'),  # Survey List for Survey Takers
    path('take_survey/<int:survey_id>/', views.take_survey, name='take_survey'),  # Survey-taking page
    path('survey_results/<int:survey_id>/', views.survey_results, name='survey_results'),  # Display survey results for creators
    path('completion_message/', views.completion_message, name='completion_message'),  # Survey completion confirmation page
    path('add_option/<int:question_id>/', views.add_option, name='add_option'),  # Add options to a question
    path('logout/', views.logout_view, name='logout'),

]
