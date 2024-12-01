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
    list_display = ('name', 'status', 'created_at', 'updated_at', 'get_total_responses', 'display_survey_results')
    search_fields = ('name',)
    inlines = [QuestionInline]  # Display questions and options in the survey admin page

    # Method to calculate the total number of responses for the survey
    def get_total_responses(self, obj):
        return obj.responses.count()  # Count of responses for the survey
    get_total_responses.short_description = 'Total Responses'

    # Method to display the survey results in a well-structured format
    def display_survey_results(self, obj):
        results = []
        question_number = 1  # To display question numbers

        # Iterate through each question in the survey
        for question in obj.questions.all():
            options_data = []
            total_responses = 0

            # Calculate the total number of responses for the question
            for option in question.options.all():
                total_responses += option.answers.count()

            # Format the question title
            question_text = f"Question {question_number}: {question.text}"
            options_data.append(question_text)
            
            # Iterate through each option and calculate its percentage
            for option in question.options.all():
                selected_count = option.answers.count()
                percentage = (selected_count / total_responses * 100) if total_responses > 0 else 0
                options_data.append(f"• {option.text}: {selected_count} Users ({percentage:.0f}%)")

            results.append("<br>".join(options_data))  # Join the options data with line breaks
            question_number += 1  # Increment the question number for the next question

        # Use mark_safe to ensure the HTML is rendered correctly in the admin panel
        return mark_safe("<br><br>".join(results)) if results else "No Responses Yet"  # Use <br><br> for better spacing between questions

    display_survey_results.short_description = 'Survey Results'

    list_filter = ('status',)

# Custom Admin for Question
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'survey', 'get_option_counts', 'get_response_percentage')
    search_fields = ('text',)

    def get_option_counts(self, obj):
        options = obj.options.all()
        return ", ".join([f"{option.text}: {option.answers.count()} responses" for option in options])
    get_option_counts.short_description = 'Option Counts'

    def get_response_percentage(self, obj):
        percentages = obj.get_response_percentage()
        return ", ".join([f"{option}: {percentage}%" for option, percentage in percentages.items()])
    get_response_percentage.short_description = 'Option Percentages'

# Custom Admin for Option
class OptionAdmin(admin.ModelAdmin):
    list_display = ('text', 'question', 'get_response_count')
    search_fields = ('text',)

    def get_response_count(self, obj):
        return obj.answers.count()  # Count of answers that selected this option
    get_response_count.short_description = 'Response Count'

# Register the models with the custom admin classes
admin.site.register(Survey, SurveyAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Option, OptionAdmin)
admin.site.register(Answer)
admin.site.register(Response)
