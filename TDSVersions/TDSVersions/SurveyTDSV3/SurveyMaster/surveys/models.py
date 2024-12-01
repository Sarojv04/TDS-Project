from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class Survey(models.Model):
    DRAFT = 'draft'
    PUBLISHED = 'published'
    CLOSED = 'closed'

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
    is_deleted = models.BooleanField(default=False)
    archived = models.BooleanField(default=False)

    def __str__(self):
        return f"Survey: {self.name} (Status: {self.status})"

    def is_published(self):
        """Check if the survey is published."""
        return self.status == self.PUBLISHED

    def clean(self):
        """Ensure logical state transitions for surveys."""
        if self.status == self.CLOSED and self.responses.exists():
            raise ValidationError("Cannot close a survey that has existing responses.")
        if self.is_deleted and self.status != self.DRAFT:
            raise ValidationError("Only draft surveys can be deleted.")

    def soft_delete(self):
        """Soft delete the survey and its associated questions and options."""
        self.is_deleted = True
        self.questions.update(is_deleted=True)
        self.save()
        print(f"Soft deleted survey: {self.name}")

    def restore(self):
        """Restore a soft-deleted survey and its associated questions and options."""
        self.is_deleted = False
        self.questions.update(is_deleted=False)
        self.save()
        print(f"Restored survey: {self.name}")

    def archive(self):
        """Mark a survey as archived."""
        self.archived = True
        self.save()
        print(f"Archived survey: {self.name}")


class Question(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()
    QUESTION_TYPES = (
        ('multiple_choice', 'Multiple Choice'),
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

    def soft_delete(self):
        """Soft delete the question and its associated options."""
        self.is_deleted = True
        self.options.update(is_deleted=True)
        self.save()
        print(f"Soft deleted question: {self.text}")

    def restore(self):
        """Restore a soft-deleted question and its associated options."""
        self.is_deleted = False
        self.options.update(is_deleted=False)
        self.save()
        print(f"Restored question: {self.text}")


class Option(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="options")
    text = models.CharField(max_length=255)
    position = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['position']

    def __str__(self):
        return f"Option: {self.text} (Question: {self.question.text})"

    def clean(self):
        """Ensure options have valid data."""
        if not self.text.strip():
            raise ValidationError("Option text cannot be empty.")

    def save(self, *args, **kwargs):
        """Ensure options are assigned a position if not provided."""
        if not self.position:
            max_position = self.question.options.aggregate(models.Max('position'))['position__max'] or 0
            self.position = max_position + 1
        super().save(*args, **kwargs)
        print(f"Saved option: {self.text}")


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

    def soft_delete(self):
        """Soft delete the response."""
        self.answers.update(is_deleted=True)
        self.save()
        print(f"Soft deleted response: {self.id}")


class Answer(models.Model):
    response = models.ForeignKey(Response, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    text = models.TextField(blank=True, null=True)
    selected_option = models.ForeignKey(Option, on_delete=models.CASCADE, blank=True, null=True, related_name="answers")

    class Meta:
        unique_together = ('response', 'question')

    def __str__(self):
        answer = self.text or self.selected_option.text if self.selected_option else "No answer"
        return f"Answer: {answer} (Question: {self.question.text})"

    def clean(self):
        """Ensure only one type of answer is provided."""
        if self.text and self.selected_option:
            raise ValidationError("Cannot provide both text and selected option as an answer.")
        if not self.text and not self.selected_option:
            raise ValidationError("An answer must be provided.")

    def soft_delete(self):
        """Soft delete the answer."""
        self.is_deleted = True
        self.save()
        print(f"Soft deleted answer: {self.id}")
