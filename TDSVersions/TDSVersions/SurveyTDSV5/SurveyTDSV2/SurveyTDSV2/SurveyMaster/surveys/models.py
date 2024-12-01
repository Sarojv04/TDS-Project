from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class Survey(models.Model):
    DRAFT = 'draft'
    PUBLISHED = 'published'
    REPUBLISHED = 'republished'
    CLOSED = 'closed'

    STATUS_CHOICES = [
        (DRAFT, 'Draft'),
        (PUBLISHED, 'Published'),
        (REPUBLISHED, 'Republished'),
        (CLOSED, 'Closed'),
    ]

    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_surveys")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default=DRAFT)
    is_deleted = models.BooleanField(default=False)
    archived = models.BooleanField(default=False)

    def __str__(self):
        return f"Survey: {self.name} (Status: {self.status})"

    def is_published(self):
        """Check if the survey is published."""
        return self.status == self.PUBLISHED

    def is_republished(self):
        """Check if the survey is republished."""
        return self.status == self.REPUBLISHED

    def get_total_responses(self):
        """Return total number of responses for this survey."""
        return self.responses.count()

    def get_published_results(self):
        """Return results for published surveys."""
        results = {}
        if self.is_published():
            for question in self.questions.filter(is_deleted=False):
                options = question.options.filter(is_deleted=False)
                total_responses = sum(option.answers.count() for option in options)
                results[question.text] = [
                    {
                        'option': option.text,
                        'count': option.answers.count(),
                        'percentage': round((option.answers.count() / total_responses) * 100, 2) if total_responses > 0 else 0,
                    }
                    for option in options
                ]
        return results

    def get_aggregated_results(self):
        """
        Return aggregated response statistics for republished surveys.
        Each question will display its options and the count of responses,
        sorted in descending order by the number of responses.
        """
        if not self.is_republished():
            return {}
        
        results = {}
        for question in self.questions.all():
            options = question.options.all()
            total_responses = sum(option.answers.count() for option in options)
            option_stats = [
                {
                    'option': option.text,
                    'count': option.answers.count(),
                    'percentage': round((option.answers.count() / total_responses) * 100, 2) if total_responses > 0 else 0,
                }
                for option in options
            ]
            # Sort options by the number of responses in descending order
            results[question.text] = sorted(option_stats, key=lambda x: x['count'], reverse=True)
        return results

    def get_survey_status(self):
        """Return the survey status as a human-readable string."""
        return dict(self.STATUS_CHOICES).get(self.status, "Unknown")

    def clean(self):
        """Ensure logical state transitions for surveys."""
        if self.status == self.CLOSED and self.responses.exists():
            raise ValidationError("Cannot close a survey that has existing responses.")
        if self.is_deleted and self.status != self.DRAFT:
            raise ValidationError("Only draft surveys can be deleted.")
        if self.status == self.REPUBLISHED and self.responses.exists() and not self.get_total_responses():
            raise ValidationError("Cannot republish a survey without responses.")

    def soft_delete(self):
        """Soft delete the survey along with its associated questions and options."""
        self.is_deleted = True
        self.questions.update(is_deleted=True)
        self.save()

    def restore(self):
        """Restore a soft-deleted survey and its associated questions and options."""
        self.is_deleted = False
        self.questions.update(is_deleted=False)
        self.save()

    def archive(self):
        """Mark a survey as archived."""
        self.archived = True
        self.save()


class Question(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()
    QUESTION_TYPES = (
        ('radio', 'Radio'),  # Changed 'multiple_choice' to 'radio'
        ('checkbox', 'Checkbox'),
        ('text', 'Text'),
    )
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    position = models.PositiveIntegerField(default=1)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ['position']

    def __str__(self):
        return f"Question: {self.text} (Survey: {self.survey.name})"

    def clean(self):
        """Ensure questions have valid data."""
        if not self.text.strip():
            raise ValidationError("Question text cannot be empty.")
        if self.question_type in ['radio', 'checkbox'] and not self.has_valid_options():
            raise ValidationError(f"{self.get_question_type_display()} questions must have at least one option.")

    def soft_delete(self):
        """Soft delete the question and its associated options."""
        self.is_deleted = True
        self.options.update(is_deleted=True)
        self.save()

    def restore(self):
        """Restore a soft-deleted question and its associated options."""
        self.is_deleted = False
        self.options.update(is_deleted=False)
        self.save()

    def get_option_counts(self):
        """Show the count of responses for each option."""
        options = self.options.all()
        return [(option.text, option.answers.count()) for option in options]

    def get_response_percentage(self, sort_by_count=True):
        """
        Calculate the percentage of responses for each option.
        If `sort_by_count` is True, sort the results by the count in descending order.
        """
        total_responses = Answer.objects.filter(question=self).count()
        if total_responses == 0:
            return {}

        percentages = {}
        for option in self.options.all():
            response_count = option.answers.count()
            percentage = (response_count / total_responses) * 100
            percentages[option.text] = {
                'count': response_count,
                'percentage': round(percentage, 2)
            }

        if sort_by_count:
            return dict(sorted(percentages.items(), key=lambda item: item[1]['count'], reverse=True))

        return percentages

    def get_aggregated_data(self):
        """
        Return aggregated data for the question.
        Each option includes its text, count of responses, and response percentage.
        """
        total_responses = Answer.objects.filter(question=self).count()
        if total_responses == 0:
            return []

        aggregated_data = []
        for option in self.options.all():
            response_count = option.answers.count()
            percentage = (response_count / total_responses * 100) if total_responses > 0 else 0
            aggregated_data.append({
                'option': option.text,
                'count': response_count,
                'percentage': round(percentage, 2),
            })

        # Sort by count in descending order
        return sorted(aggregated_data, key=lambda x: x['count'], reverse=True)

    def has_valid_options(self):
        """Check if the question has at least one valid option."""
        return self.options.filter(is_deleted=False).exists()

    def get_question_type_display(self):
        """Return the human-readable name for the question type."""
        return dict(self.QUESTION_TYPES).get(self.question_type, "Unknown")


class Option(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="options")
    text = models.CharField(max_length=255)
    position = models.PositiveIntegerField(default=1)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ['position']

    def __str__(self):
        return f"Option: {self.text} (Question: {self.question.text})"

    def clean(self):
        """Ensure options have valid data."""
        if not self.text.strip():
            raise ValidationError("Option text cannot be empty.")
        if self.question.options.filter(text__iexact=self.text).exclude(id=self.id).exists():
            raise ValidationError(f"Duplicate option text: '{self.text}' is already used in this question.")
        if self.position <= 0:
            raise ValidationError("Position must be a positive integer.")

    def save(self, *args, **kwargs):
        """Ensure options are assigned a valid position if not provided."""
        if not self.position or self.position <= 0:
            max_position = self.question.options.aggregate(models.Max('position'))['position__max'] or 0
            self.position = max_position + 1
        super().save(*args, **kwargs)

    def get_response_count(self):
        """Get the total number of responses for this option."""
        return self.answers.count()

    def get_response_percentage(self):
        """Calculate the percentage of responses for this option within its question."""
        total_responses = Answer.objects.filter(question=self.question).count()
        if total_responses == 0:
            return 0
        return round((self.get_response_count() / total_responses) * 100, 2)


class Response(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name="responses")
    taker = models.ForeignKey(User, on_delete=models.CASCADE, related_name="responses")
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Response: {self.taker.username} for Survey: {self.survey.name}"

    def clean(self):
        """Ensure responses are valid and follow survey rules."""
        if self.survey.status not in [Survey.PUBLISHED, Survey.REPUBLISHED]:
            raise ValidationError("Responses can only be submitted for published or republished surveys.")
        if Response.objects.filter(survey=self.survey, taker=self.taker).exclude(id=self.id).exists():
            raise ValidationError("A user can only submit one response per survey.")

    def get_answers_summary(self):
        """
        Return a summary of answers for this response.
        Includes the question text and the corresponding answers (text or selected option).
        """
        answers = self.answers.all()
        summary = []
        for answer in answers:
            if answer.text:
                summary.append({'question': answer.question.text, 'answer': answer.text})
            elif answer.selected_option:
                summary.append({'question': answer.question.text, 'answer': answer.selected_option.text})
        return summary

    def get_survey_status(self):
        """Retrieve the status of the survey associated with this response."""
        return self.survey.status


class Answer(models.Model):
    response = models.ForeignKey(Response, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    text = models.TextField(blank=True, null=True)
    selected_option = models.ForeignKey(Option, on_delete=models.CASCADE, blank=True, null=True, related_name="answers")

    class Meta:
        unique_together = ('response', 'question')

    def __str__(self):
        question_type = self.question.question_type
        answer = self.text or self.selected_option.text if self.selected_option else "No answer"
        return f"Answer: {answer} (Question: {self.question.text}, Type: {question_type})"

    def clean(self):
        """Ensure only one type of answer is provided and it matches the question type."""
        if self.text and self.selected_option:
            raise ValidationError("Cannot provide both text and selected option as an answer.")
        if not self.text and not self.selected_option:
            raise ValidationError("An answer must be provided.")

        # Validate answer based on the question type
        if self.question.question_type == 'text' and not self.text:
            raise ValidationError("This question requires a text answer.")
        if self.question.question_type in ['radio', 'checkbox'] and not self.selected_option:
            raise ValidationError("This question requires a selected option.")

    def get_display_answer(self):
        """
        Return a human-readable format of the answer.
        Useful for displaying answers in templates or reports.
        """
        if self.text:
            return self.text
        if self.selected_option:
            return self.selected_option.text
        return "No answer provided"
