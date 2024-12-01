from django import forms
from .models import Survey, Question, Option


# Form for creating and updating surveys
class SurveyForm(forms.ModelForm):
    class Meta:
        model = Survey
        fields = ['name', 'description', 'status']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter survey name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter survey description'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean_name(self):
        """Ensure the survey name is unique and not soft-deleted."""
        name = self.cleaned_data.get('name')
        if Survey.objects.filter(name=name, is_deleted=False).exists():
            raise forms.ValidationError("A survey with this name already exists.")
        return name


# Form for adding or editing questions in a survey
class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text', 'question_type']
        widgets = {
            'text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter question text'}),
            'question_type': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean_text(self):
        """Ensure the question text is not empty."""
        text = self.cleaned_data.get('text')
        if not text.strip():
            raise forms.ValidationError("Question text cannot be empty.")
        return text


# Form for adding or editing options for a question
class OptionForm(forms.ModelForm):
    class Meta:
        model = Option
        fields = ['text']
        widgets = {
            'text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter option text'}),
        }

    def __init__(self, *args, **kwargs):
        self.question = kwargs.pop('question', None)
        super().__init__(*args, **kwargs)

    def clean_text(self):
        """Ensure the option text is unique within the same question."""
        text = self.cleaned_data.get('text')
        if self.question and self.question.options.filter(text=text).exists():
            raise forms.ValidationError("This option already exists for this question.")
        return text


# Form for taking a survey
class TakeSurveyForm(forms.Form):
    def __init__(self, *args, **kwargs):
        questions = kwargs.pop('questions', None)
        super().__init__(*args, **kwargs)
        if questions:
            for question in questions:
                field_name = f'question_{question.id}'
                if question.question_type == 'text':
                    self.fields[field_name] = forms.CharField(
                        label=question.text,
                        widget=forms.TextInput(attrs={'class': 'form-control'}),
                        required=True  # Make text questions mandatory by default
                    )
                elif question.question_type == 'multiple_choice':
                    self.fields[field_name] = forms.ChoiceField(
                        label=question.text,
                        choices=[(option.id, option.text) for option in question.options.all()],
                        widget=forms.RadioSelect,
                        required=True
                    )
                elif question.question_type == 'checkbox':
                    self.fields[field_name] = forms.MultipleChoiceField(
                        label=question.text,
                        choices=[(option.id, option.text) for option in question.options.all()],
                        widget=forms.CheckboxSelectMultiple,
                        required=True
                    )

    def clean(self):
        """Ensure mandatory questions are answered."""
        cleaned_data = super().clean()
        for field_name, value in cleaned_data.items():
            if value is None or value == "":
                raise forms.ValidationError(f"Please answer all required questions.")
        return cleaned_data
