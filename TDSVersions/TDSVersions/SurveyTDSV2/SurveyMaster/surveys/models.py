from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class Survey(models.Model):
    DRAFT = 'draft'
    PUBLISHED = 'published'
    CLOSED = 'closed'  # State for surveys that are no longer active

    STATUS_CHOICES = [
        (DRAFT, 'Draft'),
        (PUBLISHED, 'Published'),
        (CLOSED, 'Closed'),
    ]

    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_surveys")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=DRAFT)
    is_deleted = models.BooleanField(default=False)  # Handle soft deletion

    def __str__(self):
        return f"Survey: {self.name} (Status: {self.status})"

    def is_published(self):
        """Check if the survey is published."""
        return self.status == self.PUBLISHED

    def clean(self):
        """Ensure logical state transitions for surveys."""
        if self.status == self.CLOSED and self.responses.exists():
            raise ValidationError("Cannot close a survey that has existing responses.")

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


class Question(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()
    QUESTION_TYPES = (
        ('multiple_choice', 'Multiple Choice'),
        ('checkbox', 'Checkbox'),
        ('text', 'Text'),
    )
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    is_deleted = models.BooleanField(default=False)  # Handle soft deletion

    def __str__(self):
        return f"Question: {self.text} (Survey: {self.survey.name})"

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


class Option(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="options")
    text = models.CharField(max_length=255)

    def __str__(self):
        return f"Option: {self.text} (Question: {self.question.text})"


class Response(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name="responses")
    taker = models.ForeignKey(User, on_delete=models.CASCADE, related_name="responses")
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Response: {self.taker.username} for Survey: {self.survey.name}"

    def clean(self):
        """Ensure responses are only for published surveys."""
        if self.survey.status != Survey.PUBLISHED:
            raise ValidationError("Responses can only be submitted for published surveys.")


class Answer(models.Model):
    response = models.ForeignKey(Response, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    text = models.TextField(blank=True, null=True)  # For text answers
    selected_option = models.ForeignKey(Option, on_delete=models.CASCADE, blank=True, null=True)  # For multiple choice or checkbox

    def __str__(self):
        answer = self.text or self.selected_option.text if self.selected_option else "No answer"
        return f"Answer: {answer} (Question: {self.question.text})"

    def clean(self):
        """Ensure only one type of answer is provided."""
        if self.text and self.selected_option:
            raise ValidationError("Cannot provide both text and selected option as an answer.")
        if not self.text and not self.selected_option:
            raise ValidationError("An answer must be provided.")
