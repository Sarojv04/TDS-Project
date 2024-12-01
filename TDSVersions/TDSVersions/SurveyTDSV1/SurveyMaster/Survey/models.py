from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now  # Added for default timestamps


# UserProfile to manage roles (Survey Creator / Survey Taker)
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(
        max_length=10,
        choices=[('creator', 'Survey Creator'), ('taker', 'Survey Taker')],
        default='taker',
    )

    def __str__(self):
        return f"{self.user.username} ({self.role})"


# Survey Model to store Survey details
class Survey(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_surveys')  # Link to Survey Creator
    status = models.CharField(
        max_length=10,
        choices=[('Draft', 'Draft'), ('Published', 'Published'), ('Closed', 'Closed')],
        default='Draft',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(null=True, blank=True)  # Optional field to track publish date

    def __str__(self):
        return self.name


# Question Model to store questions for each survey
class Question(models.Model):
    survey = models.ForeignKey(Survey, related_name='questions', on_delete=models.CASCADE)  # Link to Survey
    text = models.CharField(max_length=300)  # Question text
    question_type = models.CharField(
        max_length=10,
        choices=[('Radio', 'Radio'), ('Checkbox', 'Checkbox')],
        default='Radio',
    )

    def __str__(self):
        return self.text


# Option Model to store individual options for a question
class Option(models.Model):
    question = models.ForeignKey(Question, related_name='options', on_delete=models.CASCADE)
    text = models.CharField(max_length=200)  # Option text

    def __str__(self):
        return f"{self.text} (Question: {self.question.text})"



# Response Model to store responses from Survey Takers
class Response(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='responses')  # Link to Question
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='responses')  # Link to User (Survey Taker)
    selected_option = models.ForeignKey(Option, on_delete=models.CASCADE, related_name='responses')  # Selected Option
    created_at = models.DateTimeField(auto_now_add=True)  # Automatically set when the response is created

    def __str__(self):
        return f"Response by {self.user.username} to question {self.question.text}"
