from django.contrib import admin
from .models import Survey, Question, Response, UserProfile, Option

# Survey Admin Configuration
class SurveyAdmin(admin.ModelAdmin):
    list_display = ('name', 'creator', 'status', 'created_at')  # Display relevant fields in the list view
    list_filter = ('status',)  # Filter by survey status (Draft, Published, Closed)
    search_fields = ('name',)  # Enable searching by survey name

# Question Admin Configuration
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'survey', 'question_type')  # Display question text, survey, and type
    search_fields = ('text',)  # Enable searching by question text

# Option Admin Configuration
class OptionAdmin(admin.ModelAdmin):
    list_display = ('text', 'question')  # Show option text and associated question
    search_fields = ('text', 'question__text')  # Enable searching by option text or question text

# Response Admin Configuration
class ResponseAdmin(admin.ModelAdmin):
    list_display = ('question', 'user', 'selected_option')  # Show which user answered which question and the selected option
    list_filter = ('question', 'user')  # Filter responses by question and user
    search_fields = ('user__username',)  # Search by username of the responder

# UserProfile Admin Configuration
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')  # Display user and role in the admin panel
    search_fields = ('user__username',)  # Enable searching by username

# Register models with customized admin configuration
admin.site.register(Survey, SurveyAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Option, OptionAdmin)  # Register Option model
admin.site.register(Response, ResponseAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
