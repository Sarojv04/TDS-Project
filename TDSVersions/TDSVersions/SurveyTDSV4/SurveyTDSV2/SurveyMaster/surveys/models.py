from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class Survey(models.Model):
    DRAFT = 'draft'
    PUBLISHED = 'published'
    CLOSED = 'closed'
    REPUBLISHED = 'republished'  # New status for republished surveys

    STATUS_CHOICES = [
        (DRAFT, 'Draft'),
        (PUBLISHED, 'Published'),
        (CLOSED, 'Closed'),
        (REPUBLISHED, 'Republished'),  # Adding Republished status
    ]

    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_surveys")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=11, choices=STATUS_CHOICES, default=DRAFT)
    is_deleted = models.BooleanField(default=False)
    archived = models.BooleanField(default=False)
    republished = models.BooleanField(default=False)  # New field for republishing
    republished_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Survey: {self.name} (Status: {self.status})"

    def is_published(self):
        """Check if the survey is published."""
        return self.status == self.PUBLISHED or self.status == self.REPUBLISHED

    def get_total_responses(self):
        """Return total number of responses for this survey."""
        return self.responses.count()

    def get_aggregated_statistics(self):
        """Return aggregated statistics for republished surveys."""
        if self.republished:
            stats = {}
            for question in self.questions.all():
                stats[question.text] = question.get_response_percentage()  # Aggregated percentages
            return stats
        return {}

    def republish(self):
        """Set the survey to republished mode and mark it as active for responses."""
        self.republished = True
        self.status = self.REPUBLISHED  # Change status to republished
        self.save()

    def clean(self):
        """Ensure logical state transitions for surveys."""
        if self.status == self.CLOSED and self.responses.exists():
            raise ValidationError("Cannot close a survey that has existing responses.")
        if self.is_deleted and self.status != self.DRAFT:
            raise ValidationError("Only draft surveys can be deleted.")

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

    def restore(self):
        """Restore a soft-deleted question and its associated options."""
        self.is_deleted = False
        self.options.update(is_deleted=False)
        self.save()

    def get_option_counts(self):
        """Show the count of responses for each option."""
        options = self.options.all()
        return [(option.text, option.answers.count()) for option in options]

    def get_response_percentage(self):
        """Calculate the percentage of responses for each option."""
        total_responses = Answer.objects.filter(question=self).count()
        if total_responses == 0:
            return {}
        options = self.options.all()
        percentages = {}
        for option in options:
            response_count = option.answers.count()
            percentage = (response_count / total_responses) * 100
            percentages[option.text] = round(percentage, 2)
        return percentages


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
