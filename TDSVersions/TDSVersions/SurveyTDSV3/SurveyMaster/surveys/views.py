import logging
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.middleware.csrf import get_token
from .models import Survey, Question, Option, Response, Answer

logger = logging.getLogger(__name__)

# Homepage
def homepage(request):
    """Render the homepage."""
    logger.info("Rendering the homepage.")
    return render(request, 'surveys/homepage.html', {'page_title': 'Home Page'})

# Register Page
def register(request):
    """Handle user registration."""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Account created successfully for {user.username}!")
            logger.info(f"User {user.username} registered successfully.")
            return redirect('login')
        else:
            logger.warning("Registration form contains errors.")
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserCreationForm()
    return render(request, 'surveys/register.html', {'form': form, 'page_title': 'Register Page'})

# Login Page
from django.middleware.csrf import get_token
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login
from django.contrib import messages
from django.urls import reverse

def login(request):
    """Handle user login."""
    if request.method == 'GET':
        # Generate CSRF token for the GET request
        csrf_token = get_token(request)
        logger.debug(f"Generated CSRF Token (GET request): {csrf_token}")

    if request.method == 'POST':
        # Retrieve username and password from the form
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Authenticate user
        user = authenticate(request, username=username, password=password)

        if user:
            # Log in the authenticated user
            auth_login(request, user)
            logger.info(f"User {user.username} logged in successfully.")

            # Redirect to the appropriate dashboard
            if user.is_staff:
                return redirect('surveys:creator_dashboard')  # Redirect to creator dashboard
            else:
                return redirect('surveys:taker_dashboard')  # Redirect to taker dashboard
        else:
            logger.warning(f"Authentication failed for username={username}.")
            messages.error(request, "Invalid username or password!")

    # Render the login form
    return render(request, 'surveys/login.html', {'page_title': 'Login Page'})



# Logout
def logout_view(request):
    """Handle user logout."""
    logger.info(f"User {request.user.username} logged out.")
    logout(request)
    messages.success(request, "Logged out successfully!")
    return redirect('homepage')

# Creator Dashboard
def creator_dashboard(request):
    """Render the creator dashboard for staff users."""
    if not request.user.is_authenticated:
        messages.error(request, "Please log in to access the dashboard.")
        return redirect('login')

    if not request.user.is_staff:
        messages.error(request, "Access denied!")
        return redirect('taker_dashboard')

    try:
        if request.user.is_superuser:
            drafts = Survey.objects.filter(status='draft', is_deleted=False).select_related('creator')
            published = Survey.objects.filter(status='published', is_deleted=False).select_related('creator')
            closed = Survey.objects.filter(status='closed', is_deleted=False).select_related('creator')
        else:
            drafts = Survey.objects.filter(creator=request.user, status='draft', is_deleted=False)
            published = Survey.objects.filter(creator=request.user, status='published', is_deleted=False)
            closed = Survey.objects.filter(creator=request.user, status='closed', is_deleted=False)

        logger.info(f"Dashboard data loaded for user {request.user.username}. Drafts: {drafts.count()}, "
                    f"Published: {published.count()}, Closed: {closed.count()}")

    except Exception as e:
        logger.error(f"Error loading dashboard data: {e}")
        messages.error(request, "An error occurred while loading the dashboard.")

    return render(request, 'surveys/creator_dashboard.html', {
        'page_title': 'Creator Dashboard',
        'drafts': drafts,
        'published': published,
        'closed': closed,
        'is_superuser': request.user.is_superuser,
    })

# Taker Dashboard
def taker_dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.user.is_staff:
        return redirect('creator_dashboard')

    surveys = Survey.objects.filter(status='published', is_deleted=False).select_related('creator')
    logger.info(f"Loading taker dashboard for user {request.user.username}. Published surveys: {surveys.count()}")
    return render(request, 'surveys/taker_dashboard.html', {'page_title': 'Taker Dashboard', 'surveys': surveys})



# Survey List for Takers
def survey_list(request):
    """List all available surveys."""
    if not request.user.is_authenticated:
        return redirect('login')

    surveys = Survey.objects.filter(status='published', is_deleted=False)
    return render(request, 'surveys/survey_list.html', {'page_title': 'Available Surveys', 'surveys': surveys})


# Create Survey
def create_survey(request):
    """Allow creators to create new surveys."""
    if not request.user.is_authenticated or not request.user.is_staff:
        messages.error(request, "Access denied!")
        return redirect('login')

    if request.method == "POST":
        # Capture survey data
        survey_name = request.POST.get('survey_name', '').strip()
        description = request.POST.get('description', '').strip()
        action = request.POST.get('action', 'draft')  # 'draft' or 'publish'

        if survey_name:
            try:
                # Create the survey
                survey = Survey.objects.create(
                    name=survey_name,
                    description=description,
                    status='published' if action == 'publish' else 'draft',
                    creator=request.user,
                )
                print(f"Survey Created: {survey}")

                # Save questions and options
                question_count = 0
                for key in request.POST.keys():
                    if key.startswith('questions[') and key.endswith('][text]'):
                        question_count += 1
                        question_text = request.POST.get(key, '').strip()
                        question_key = key.split('[')[1].split(']')[0]
                        question_type = request.POST.get(f"questions[{question_key}][type]", 'multiple_choice').strip()

                        if question_text:
                            question = question.objects.create(
                                survey=survey,
                                text=question_text,
                                question_type=question_type,
                            )
                            print(f"Question Saved: {question.text}")

                            # Save options if the question type requires them
                            if question_type in ["multiple_choice", "checkbox"]:
                                options = request.POST.getlist(f"questions[{question_key}][options][]")
                                if not options:
                                    raise ValueError(f"Question '{question_text}' requires at least one option.")
                                for option_text in options:
                                    if option_text.strip():
                                        options.objects.create(
                                            question=question,
                                            text=option_text.strip(),
                                        )
                                        print(f"Option Saved: {option_text.strip()}")

                if question_count == 0:
                    survey.delete()  # Rollback survey if no questions were added
                    messages.error(request, "You must add at least one question to the survey.")
                    return redirect('create_survey')

                # Display success message
                messages.success(request, f"Survey '{survey.name}' saved as {survey.status}!")
                return redirect('creator_dashboard')

            except Exception as e:
                print(f"Error Creating Survey: {e}")
                messages.error(request, "An error occurred while creating the survey.")
                return redirect('create_survey')
        else:
            messages.error(request, "Survey name cannot be empty!")

    return render(request, 'surveys/create_survey.html', {'page_title': 'Create Survey'})


logger = logging.getLogger(__name__)  # Setup a logger for debugging



# Edit Survey

def edit_survey(request, survey_id):
    """Allow creators to edit existing surveys and their options."""
    if not request.user.is_authenticated or not request.user.is_staff:
        messages.error(request, "Access denied!")
        return redirect('login')

    # Fetch the survey
    survey = get_object_or_404(Survey, id=survey_id, creator=request.user, is_deleted=False)

    # Fetch related questions
    questions = survey.questions.all()

    if request.method == "POST":
        # Update survey details
        survey.name = request.POST.get('survey_name', survey.name)
        survey.description = request.POST.get('description', survey.description)
        survey.save()

        # Process each question from the POST data
        for key, value in request.POST.items():
            if key.startswith("questions[") and key.endswith("][text]"):
                question_id = key.split('[')[1].split(']')[0]

                # Handle new and existing questions
                if question_id.startswith("new_"):
                    # Create a new question
                    question = Question.objects.create(
                        survey=survey,
                        text=value.strip(),
                        question_type=request.POST.get(f"questions[{question_id}][type]", "text"),
                        position=len(questions) + 1,
                    )
                else:
                    # Update an existing question
                    try:
                        question = Question.objects.get(id=question_id, survey=survey)
                        question.text = value.strip()
                        question.question_type = request.POST.get(f"questions[{question_id}][type]", question.question_type)
                        question.save()
                    except Question.DoesNotExist:
                        continue

                # Process options for the question
                options_key = f"questions[{question_id}][options][]"
                if options_key in request.POST:
                    # Remove existing options (if any) before saving updated ones
                    question.options.all().delete()

                    for option_text in request.POST.getlist(options_key):
                        if option_text.strip():
                            Option.objects.create(question=question, text=option_text.strip())

        # Handle survey status
        action = request.POST.get('action')
        if action == "save_draft":
            survey.status = Survey.DRAFT
        elif action == "publish":
            survey.status = Survey.PUBLISHED
        survey.save()

        messages.success(request, f"Survey '{survey.name}' has been updated!")
        return redirect('creator_dashboard')

    return render(request, 'surveys/edit_survey.html', {
        'survey': survey,
        'questions': questions,
        'page_title': f"Edit Survey - {survey.name}",
    })


# Delete Survey
def delete_survey(request, survey_id):
    """Soft delete a survey."""
    if not request.user.is_authenticated or not request.user.is_staff:
        messages.error(request, "Access denied!")
        return redirect('login')

    survey = get_object_or_404(Survey, id=survey_id, creator=request.user)
    survey.is_deleted = True
    survey.save()
    messages.success(request, f"Survey '{survey.name}' has been deleted successfully!")
    return redirect('creator_dashboard')


# Close Survey
def close_survey(request, survey_id):
    """Allow creators to close a survey."""
    if not request.user.is_authenticated or not request.user.is_staff:
        messages.error(request, "Access denied! Only staff members can perform this action.")
        return redirect('login')

    try:
        # Attempt to retrieve the survey created by the logged-in staff user
        survey = get_object_or_404(Survey, id=survey_id, creator=request.user, is_deleted=False)

        # Check if the survey is already closed
        if survey.status == 'closed':
            messages.warning(request, f"Survey '{survey.name}' is already closed.")
        else:
            # Update the survey status to 'closed'
            survey.status = 'closed'
            survey.save()
            messages.success(request, f"Survey '{survey.name}' has been closed successfully!")

    except Exception as e:
        # Log any unexpected errors
        print(f"Error closing survey: {e}")
        messages.error(request, "An error occurred while attempting to close the survey.")

    # Redirect to the creator dashboard
    return redirect('creator_dashboard')


# Take Survey
def take_survey(request, survey_id):
    if not request.user.is_authenticated:
        return redirect('login')

    survey = get_object_or_404(Survey, id=survey_id, status='published', is_deleted=False)
    questions = survey.questions.filter(is_deleted=False).prefetch_related('options')

    if request.method == 'POST':
        print("POST Data:", request.POST)  # Debugging POST keys

        with transaction.atomic():
            response = Response.objects.create(survey=survey, taker=request.user)
            print(f"Created Response ID: {response.id}")

            for question in questions:
                print(f"Processing Question ID: {question.id}, Text: {question.text}")

                if question.question_type == 'text':
                    answer_text = request.POST.get(f"question_{question.id}", "").strip()
                    print(f"Text answer for question {question.id}: {answer_text}")
                    if answer_text:
                        Answer.objects.create(
                            response=response,
                            question=question,
                            text=answer_text
                        )

                elif question.question_type in ['radio', 'checkbox']:
                    selected_option_ids = request.POST.getlist(f"question_{question.id}")
                    print(f"Selected options for question {question.id}: {selected_option_ids}")
                    for option_id in selected_option_ids:
                        selected_option = question.options.filter(id=option_id).first()
                        if selected_option:
                            Answer.objects.create(
                                response=response,
                                question=question,
                                selected_option=selected_option
                            )

        messages.success(request, f"Your response to the survey '{survey.name}' has been submitted successfully!")
        return redirect('completion_message')

    return render(request, 'surveys/take_survey.html', {
        'page_title': f"Take Survey: {survey.name}",
        'survey': survey,
        'questions': questions,
    })

    
    


# Completion Message
def completion_message(request):
    print("Rendering completion_message.html")  # Debugging line
    return render(request, 'surveys/completion_message.html', {'page_title': 'Survey Completion'})



# Survey Results
def survey_results(request, survey_id):
    """Display the results of a specific survey."""
    if not request.user.is_authenticated or not request.user.is_staff:
        messages.error(request, "Access denied!")
        return redirect('taker_dashboard')

    survey = get_object_or_404(Survey, id=survey_id)
    questions = survey.questions.filter(is_deleted=False)

    results = []
    for question in questions:
        question_data = {
            "text": question.text,
            "type": question.question_type,
            "options": [],
        }

        if question.question_type in ['multiple_choice', 'checkbox']:
            options = question.options.all()
            total_responses = sum(option.answers.count() for option in options)
            for option in options:
                response_count = option.answers.count()
                percentage = (response_count / total_responses) * 100 if total_responses > 0 else 0
                question_data["options"].append({
                    "text": option.text,
                    "response_count": response_count,
                    "percentage": percentage,
                })
        results.append(question_data)

    return render(request, 'surveys/survey_results.html', {
        'page_title': f"Survey Results: {survey.name}",
        'survey': survey,
        'results': results,
    })



# Submit Survey

def submit_survey(request, survey_id):
    if request.method == 'POST':
        with transaction.atomic():  # Ensure all or nothing
            survey = get_object_or_404(Survey, id=survey_id, status='published', is_deleted=False)
            response = Response.objects.create(survey=survey, taker=request.user)

        # Debugging: Print incoming POST data
        print("POST Data:", request.POST)

        # Iterate through the questions
        questions = survey.questions.filter(is_deleted=False).prefetch_related('options')
        for question in questions:
            print(f"Processing Question ID: {question.id}, Text: {question.text}, Type: {question.question_type}")

            if question.question_type == 'text':
                # Handle text answers
                answer_text = request.POST.get(f"question_{question.id}", "").strip()
                if answer_text:
                    try:
                        Answer.objects.create(
                            response=response,
                            question=question,
                            text=answer_text
                        )
                        print(f"Saved text answer for question {question.id}: {answer_text}")
                    except Exception as e:
                        print(f"Failed to save text answer for Question {question.id}: {e}")

            elif question.question_type in ['radio', 'checkbox']:
                # Handle selected options
                selected_option_ids = request.POST.getlist(f"question_{question.id}")
                print(f"Selected Option IDs for Question {question.id}: {selected_option_ids}")  # Debugging
                for option_id in selected_option_ids:
                    selected_option = Option.objects.filter(id=option_id, question=question).first()
                    if selected_option:
                        try:
                            Answer.objects.create(
                                response=response,
                                question=question,
                                selected_option=selected_option
                            )
                            print(f"Saved selected option for question {question.id}: {selected_option.text}")
                        except Exception as e:
                            print(f"Failed to save selected option for Question {question.id}: {e}")

        # Display a success message
        messages.success(request, f"Your response to the survey '{survey.name}' has been submitted successfully!")
        return redirect('completion_message')
    return redirect('taker_dashboard')





# Publish Survey
def publish_survey(request, survey_id):
    """Publish a survey."""
    if not request.user.is_authenticated or not request.user.is_staff:
        messages.error(request, "Access denied!")
        return redirect('login')

    try:
        survey = get_object_or_404(Survey, id=survey_id, creator=request.user, is_deleted=False)
        if survey.status == 'draft':
            survey.status = 'published'
            survey.save()
            logger.info(f"Survey '{survey.name}' published successfully by {request.user.username}.")
            messages.success(request, f"Survey '{survey.name}' has been published!")
        else:
            logger.warning(f"Survey '{survey.name}' is already published or closed.")
            messages.warning(request, f"Survey '{survey.name}' is already published or closed.")
    except Survey.DoesNotExist:
        logger.error(f"Survey not found or access denied for user {request.user.username}.")
        messages.error(request, "Survey not found or you don't have permission to access it.")

    return redirect('creator_dashboard')