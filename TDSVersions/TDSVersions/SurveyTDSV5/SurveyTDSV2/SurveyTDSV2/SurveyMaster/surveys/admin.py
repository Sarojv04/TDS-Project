from django.utils.safestring import mark_safe  # Import mark_safe for HTML rendering
from django.contrib import admin
from .models import Survey, Question, Option, Answer, Response


# Inline Model for Options to show them within the Question
class OptionInline(admin.TabularInline):
    model = Option
    extra = 1


# Inline Model for Questions to show them within the Survey
class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    inlines = [OptionInline]


# Custom Admin for Survey
class SurveyAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'creator', 'created_at', 'updated_at', 'get_total_responses', 'display_survey_results')
    search_fields = ('name', 'creator__username')
    list_filter = ('status', 'creator__username')  # Filter surveys by status and creator
    inlines = [QuestionInline]  # Display questions and options in the survey admin page

    def get_total_responses(self, obj):
        """Calculate the total number of responses for the survey."""
        return obj.responses.count()

    get_total_responses.short_description = 'Total Responses'

    def display_survey_results(self, obj):
        """Display survey results in a formatted HTML view."""
        results = []
        question_number = 1

        for question in obj.questions.filter(is_deleted=False):
            options_data = []
            total_responses = sum(option.answers.count() for option in question.options.filter(is_deleted=False))

            # Format the question title
            question_text = f"<b>Question {question_number}: {question.text}</b>"
            options_data.append(question_text)

            # Iterate through each option
            for option in question.options.filter(is_deleted=False):  # Now filtering options based on is_deleted
                response_count = option.answers.count()
                percentage = (response_count / total_responses * 100) if total_responses > 0 else 0
                options_data.append(f"• {option.text}: {response_count} Users ({percentage:.0f}%)")

            results.append("<br>".join(options_data))
            question_number += 1

        return mark_safe("<br><br>".join(results)) if results else "No Responses Yet"

    display_survey_results.short_description = 'Survey Results'


# Custom Admin for Question
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'survey', 'question_type', 'get_option_counts', 'get_response_percentage')
    search_fields = ('text', 'survey__name')
    list_filter = ('question_type',)

    def get_option_counts(self, obj):
        """Show the count of responses for each option."""
        options = obj.options.filter(is_deleted=False)
        return ", ".join([f"{option.text}: {option.answers.count()} responses" for option in options])

    get_option_counts.short_description = 'Option Counts'

    def get_response_percentage(self, obj):
        """Display percentage of responses for each option."""
        percentages = obj.get_response_percentage()
        return ", ".join([f"{option}: {percentage}%" for option, percentage in percentages.items()])

    get_response_percentage.short_description = 'Option Percentages'


# Custom Admin for Option
class OptionAdmin(admin.ModelAdmin):
    list_display = ('text', 'question', 'get_response_count')
    search_fields = ('text', 'question__text')

    def get_response_count(self, obj):
        """Count the number of responses that selected this option."""
        return obj.answers.count()

    get_response_count.short_description = 'Response Count'


# Register the models with the custom admin classes
admin.site.register(Survey, SurveyAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Option, OptionAdmin)
admin.site.register(Answer)
admin.site.register(Response)
