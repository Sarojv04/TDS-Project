from django import forms
from .models import Survey, Question, Option


# SurveyForm for creating and editing surveys
class SurveyForm(forms.ModelForm):
    class Meta:
        model = Survey
        fields = ['name', 'description', 'status']  # Include the fields you want the creator to fill
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Enter survey name'}),
            'description': forms.Textarea(attrs={'placeholder': 'Enter survey description'}),
            'status': forms.Select(choices=[('Draft', 'Draft'), ('Published', 'Published'), ('Closed', 'Closed')]),
        }
        labels = {
            'name': 'Survey Name',
            'description': 'Description',
            'status': 'Status',
        }


# QuestionForm for creating and editing questions in a survey
class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text', 'question_type']  # Removed options as it's handled via OptionForm
        widgets = {
            'text': forms.TextInput(attrs={'placeholder': 'Enter question text'}),
            'question_type': forms.Select(choices=[('Radio', 'Radio'), ('Checkbox', 'Checkbox')]),
        }
        labels = {
            'text': 'Question Text',
            'question_type': 'Question Type',
        }


# OptionForm for creating and editing options for a question
class OptionForm(forms.ModelForm):
    class Meta:
        model = Option
        fields = ['text']  # Only the option text
        widgets = {
            'text': forms.TextInput(attrs={'placeholder': 'Enter option text'}),
        }
        labels = {
            'text': 'Option Text',
        }
