import pprint
import logging
from django.db import transaction  # To group operations and handle rollbacks if needed
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.middleware.csrf import get_token  # CSRF token debugging
from .models import Survey, Question, Option, Response, Answer
from django.db.models import Count
from .models import Survey




# Homepage
def homepage(request):
    """Render the homepage."""
    return render(request, 'surveys/homepage.html', {'page_title': 'Home Page'})


# Register Page
def register(request):
    """Handle user registration."""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Account created successfully for {user.username}!")
            return redirect('login')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserCreationForm()
    return render(request, 'surveys/register.html', {'form': form, 'page_title': 'Register Page'})


# Login Page
def login(request):
    """Handle user login."""

    # CSRF token debugging for GET requests
    if request.method == 'GET':
        csrf_token = get_token(request)
        print(f"Generated CSRF Token (GET request): {csrf_token}")

    if request.method == 'POST':
        # Extracting username and password
        username = request.POST.get('username')
        password = request.POST.get('password')
        print(f"Login attempt: username={username}, password={'*' * len(password)}")

        # Authenticate the user
        user = authenticate(request, username=username, password=password)

        if user is not None:
            auth_login(request, user)
            print(f"User {user.username} logged in successfully.")

            # Redirect based on user type
            if user.is_staff:
                return redirect('creator_dashboard')
            else:
                return redirect('taker_dashboard')
        else:
            print(f"Authentication failed for username={username}.")
            messages.error(request, "Invalid username or password!")

    return render(request, 'surveys/login.html', {'page_title': 'Login Page'})


# Logout
def logout_view(request):
    """Handle user logout."""
    logout(request)
    messages.success(request, "Logged out successfully!")
    return redirect('homepage')


# Creator Dashboard
def creator_dashboard(request):
    """Render the creator dashboard for staff users."""
    # Ensure the user is authenticated and a staff user
    if not request.user.is_authenticated:
        messages.error(request, "Please log in to access the dashboard.")
        return redirect('login')

    if not request.user.is_staff:
        messages.error(request, "Access denied! You do not have permission to access the creator dashboard.")
        return redirect('taker_dashboard')

    # If the user is a superuser, show all surveys; otherwise, show only the creator's surveys
    if request.user.is_superuser:
        drafts = Survey.objects.filter(status='draft', is_deleted=False)
        published = Survey.objects.filter(status='published', is_deleted=False)
        republished = Survey.objects.filter(status='republished', is_deleted=False)
        closed = Survey.objects.filter(status='closed', is_deleted=False)
    else:
        drafts = Survey.objects.filter(creator=request.user, status='draft', is_deleted=False)
        published = Survey.objects.filter(creator=request.user, status='published', is_deleted=False)
        republished = Survey.objects.filter(creator=request.user, status='republished', is_deleted=False)
        closed = Survey.objects.filter(creator=request.user, status='closed', is_deleted=False)

    # Added logic to handle the renamed button labels for published and republished results
    for survey in published:
        survey.button_label = "View Published Results"
    for survey in republished:
        survey.button_label = "View RePublished Results"

    # Render the dashboard with the filtered surveys
    return render(request, 'surveys/creator_dashboard.html', {
        'page_title': 'Creator Dashboard',
        'drafts': drafts,
        'published': published,
        'republished': republished,  # Pass republished surveys to the template
        'closed': closed,
        'is_superuser': request.user.is_superuser,  # For conditional logic in the template
    })





# Taker Dashboard
def taker_dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.user.is_staff:
        return redirect('creator_dashboard')

    # Retrieve published and republished surveys for the taker
    published_surveys = Survey.objects.filter(status='published', is_deleted=False)
    republished_surveys = Survey.objects.filter(status='republished', is_deleted=False)

    return render(request, 'surveys/taker_dashboard.html', {
        'page_title': 'Taker Dashboard',
        'published_surveys': published_surveys,
        'republished_surveys': republished_surveys,
    })



# Survey List for Takers
def survey_list(request):
    """List all available surveys."""
    if not request.user.is_authenticated:
        return redirect('login')

    surveys = Survey.objects.filter(status='published', is_deleted=False)
    return render(request, 'surveys/survey_list.html', {'page_title': 'Available Surveys', 'surveys': surveys})


# Create Survey
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from .models import Survey, Question, Option


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
                        question_type = request.POST.get(f"questions[{question_key}][type]", 'radio').strip()  # Change 'multiple_choice' to 'radio'

                        if question_text:
                            question = Question.objects.create(
                                survey=survey,
                                text=question_text,
                                question_type=question_type,
                            )
                            print(f"Question Saved: {question.text}")

                            # Save options if the question type requires them
                            if question_type in ["radio", "checkbox"]:  # updated to 'radio' instead of 'multiple_choice'
                                options = request.POST.getlist(f"questions[{question_key}][options][]")
                                if not options:
                                    raise ValueError(f"Question '{question_text}' requires at least one option.")
                                for option_text in options:
                                    if option_text.strip():
                                        Option.objects.create(
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
    """Allow creators to close a republished survey and move it to the closed status."""
    
    # Ensure the user is authenticated and is the creator of the survey
    if not request.user.is_authenticated:
        messages.error(request, "You must be logged in to perform this action.")
        return redirect('login')

    try:
        # Retrieve the survey created by the logged-in user
        survey = get_object_or_404(Survey, id=survey_id, creator=request.user, is_deleted=False)

        # Check if the survey is already closed
        if survey.status == 'closed':
            messages.info(request, f"Survey '{survey.name}' is already closed.")
        
        # Ensure the survey is republished before closing
        elif survey.status == 'republished':
            # Update the survey's status to 'closed'
            survey.status = 'closed'
            survey.save()
            messages.success(request, f"Survey '{survey.name}' has been closed successfully!")

        # If the survey is not republished, inform the user
        else:
            messages.warning(
                request, 
                f"Survey '{survey.name}' cannot be closed because it is in the '{survey.status}' state. Only republished surveys can be closed."
            )

    except Exception as e:
        # Log unexpected errors and provide feedback to the user
        print(f"Error closing survey: {e}")
        messages.error(request, f"An unexpected error occurred: {e}")

    # Redirect to the creator dashboard
    return redirect('creator_dashboard')



# Take Survey
def take_survey(request, survey_id):
    """
    Allow authenticated users to take a survey (published or republished).
    Handles both text and option-based questions.
    """
    # Ensure user is authenticated
    if not request.user.is_authenticated:
        messages.error(request, "You must log in to take a survey.")
        return redirect('login')

    # Fetch the survey and ensure it is published or republished
    survey = get_object_or_404(Survey, id=survey_id, status__in=['published', 'republished'], is_deleted=False)
    questions = survey.questions.filter(is_deleted=False).prefetch_related('options')

    if request.method == 'POST':
        print("POST Data:", request.POST)  # Debugging incoming POST data

        with transaction.atomic():  # Ensure atomicity for database operations
            # Create a response for the current user
            response = Response.objects.create(survey=survey, taker=request.user)
            print(f"Created Response ID: {response.id}")

            # Process each question
            for question in questions:
                print(f"Processing Question ID: {question.id}, Text: {question.text}, Type: {question.question_type}")

                if question.question_type == 'text':
                    # Handle text-based responses
                    answer_text = request.POST.get(f"question_{question.id}", "").strip()
                    print(f"Text answer for Question {question.id}: {answer_text}")
                    if answer_text:
                        Answer.objects.create(
                            response=response,
                            question=question,
                            text=answer_text
                        )

                elif question.question_type in ['radio', 'checkbox']:  # Updated 'multiple_choice' to 'radio'
                    # Handle option-based responses
                    selected_option_ids = request.POST.getlist(f"question_{question.id}")
                    print(f"Selected options for Question {question.id}: {selected_option_ids}")
                    for option_id in selected_option_ids:
                        selected_option = Option.objects.filter(id=option_id, question=question).first()
                        if selected_option:
                            Answer.objects.create(
                                response=response,
                                question=question,
                                selected_option=selected_option
                            )

        # Success message based on survey type
        survey_type = "republished" if survey.status == 'republished' else "published"
        messages.success(request, f"Your response to the {survey_type} survey '{survey.name}' has been submitted successfully!")
        return redirect('completion_message')

    # Render the survey-taking page
    return render(request, 'surveys/take_survey.html', {
        'page_title': f"Take Survey: {survey.name}",
        'survey': survey,
        'questions': questions,
    })
    
    
    
def take_republished_survey(request, survey_id):
    """Allow authenticated users to take a republished survey and save their responses."""
    # Ensure user is authenticated
    if not request.user.is_authenticated:
        messages.error(request, "You must log in to take a survey.")
        return redirect('login')

    # Fetch the republished survey
    survey = get_object_or_404(Survey, id=survey_id, status=Survey.REPUBLISHED, is_deleted=False)
    questions = survey.questions.filter(is_deleted=False)

    if request.method == 'POST':
        with transaction.atomic():  # Ensure atomicity for database operations
            # Create a response object to store the survey taker's answers
            response = Response.objects.create(survey=survey, taker=request.user)

            # Loop through each question and save answers
            for question in questions:
                # Handle text-based responses
                if question.question_type == 'text':
                    answer_text = request.POST.get(f"question_{question.id}")
                    if answer_text:
                        Answer.objects.create(
                            response=response,
                            question=question,
                            text=answer_text
                        )
                # Handle option-based responses (radio or checkbox)
                elif question.question_type in ['radio', 'multiple_choice']:
                    selected_option_ids = request.POST.getlist(f"question_{question.id}")
                    for option_id in selected_option_ids:
                        selected_option = get_object_or_404(Option, id=option_id, question=question)
                        Answer.objects.create(
                            response=response,
                            question=question,
                            selected_option=selected_option
                        )
            
            messages.success(request, "Your responses have been submitted successfully!")
            return redirect('completion_message')  # Redirect to a success page or results page

    # Prepare aggregated results for displaying the "Wisdom of the Crowd"
    aggregated_results = {}
    for question in questions:
        options_data = []
        total_responses = sum(option.answers.count() for option in question.options.all())
        for option in question.options.all():
            selected_count = option.answers.count()
            options_data.append({
                'option': option.text,
                'count': selected_count,
            })
        aggregated_results[question.id] = options_data

    # Render the survey-taking page with aggregated data
    return render(request, 'surveys/republished_survey_taker.html', {
        'survey': survey,
        'questions': questions,
        'aggregated_results': aggregated_results,
        'page_title': f"Take Republished Survey: {survey.name}",
    })

    


# Completion Message
def completion_message(request):
    print("Rendering completion_message.html")  # Debugging line
    return render(request, 'surveys/completion_message.html', {'page_title': 'Survey Completion'})



# Survey Results


def survey_results(request, survey_id):
    """Fetch and display results for a published survey."""
    survey = get_object_or_404(Survey, id=survey_id, status=Survey.PUBLISHED, is_deleted=False)
    results = []

    # Only fetch results for published surveys
    for question in survey.questions.filter(is_deleted=False):
        question_data = {
            'text': question.text,  # Question text to be displayed
            'options': []  # Options for each question
        }

        total_responses = sum(option.answers.count() for option in question.options.all())

        # Collect data for each option
        for option in question.options.all():
            selected_count = option.answers.count()
            percentage = (selected_count / total_responses * 100) if total_responses > 0 else 0
            question_data['options'].append({
                'option': option.text,  # Option text
                'count': selected_count,  # Response count
                'percentage': round(percentage, 2)  # Percentage of total responses
            })

        # Append formatted results for each question
        results.append(question_data)

    # Pass the results to the template
    return render(request, 'surveys/survey_results.html', {
        'page_title': f"Survey Results: {survey.name}",
        'survey': survey,
        'results': results,
    })





from django.db.models import Count

def aggregated_results(request, survey_id):
    """Display aggregated results for a republished survey."""
    if not request.user.is_authenticated:
        messages.error(request, "You need to log in to view aggregated results.")
        return redirect('login')

    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "Access denied! Only staff or admin users can view aggregated results.")
        return redirect('taker_dashboard')

    # Fetch the republished survey
    survey = get_object_or_404(Survey, id=survey_id, is_deleted=False, status='republished')

    # Verify the user is authorized to view the survey
    if not request.user.is_superuser and survey.creator != request.user:
        messages.error(request, "Access denied! You are not authorized to view this survey's aggregated results.")
        return redirect('creator_dashboard')

    # Prepare aggregated results for questions
    questions_with_results = []
    for question in survey.questions.all():
        options_data = []
        total_responses = Answer.objects.filter(question=question).count()

        # Calculate option counts and percentages
        for option in question.options.all():
            option_count = Answer.objects.filter(selected_option=option).count()
            percentage = (option_count / total_responses * 100) if total_responses > 0 else 0
            options_data.append({
                'option': option.text,
                'count': option_count,
                'percentage': round(percentage, 2),
            })

        # Add question and associated results
        questions_with_results.append({
            'question_text': question.text,
            'total_responses': total_responses,
            'options': options_data,
        })

    # Check for results label (View Published Results or View RePublished Results)
    results_label = "View RePublished Results"

    return render(request, 'surveys/aggregated_results.html', {
        'page_title': f"Aggregated Results: {survey.name}",
        'survey': survey,
        'questions_with_results': questions_with_results,
        'results_label': results_label,  # Dynamically pass label for the button
    })



# Submit Survey

# Logger for debugging
logger = logging.getLogger(__name__)

def submit_survey(request, survey_id):
    """
    Handle survey submission by the taker.
    This function processes both text-based and option-based responses
    and ensures data integrity with transaction management.
    """
    if request.method == 'POST':
        try:
            with transaction.atomic():  # Ensure atomicity for database operations
                # Fetch the survey and ensure it is published or republished
                survey = get_object_or_404(Survey, id=survey_id, status__in=['published', 'republished'], is_deleted=False)

                # Create a response object for the current user
                response = Response.objects.create(survey=survey, taker=request.user)

                # Debugging: Log incoming POST data
                logger.debug(f"POST Data: {request.POST}")

                # Fetch all questions related to the survey
                questions = survey.questions.filter(is_deleted=False).prefetch_related('options')

                for question in questions:
                    logger.debug(f"Processing Question ID: {question.id}, Text: {question.text}, Type: {question.question_type}")

                    if question.question_type == 'text':
                        # Process text responses
                        answer_text = request.POST.get(f"question_{question.id}", "").strip()
                        if answer_text:
                            Answer.objects.create(
                                response=response,
                                question=question,
                                text=answer_text
                            )
                            logger.debug(f"Saved text answer for Question {question.id}: {answer_text}")

                    elif question.question_type in ['radio', 'checkbox']:  # 'multiple_choice' replaced with 'radio'
                        # Process selected options for radio or checkbox questions
                        selected_option_ids = request.POST.getlist(f"question_{question.id}")
                        logger.debug(f"Selected Option IDs for Question {question.id}: {selected_option_ids}")
                        for option_id in selected_option_ids:
                            selected_option = Option.objects.filter(id=option_id, question=question).first()
                            if selected_option:
                                Answer.objects.create(
                                    response=response,
                                    question=question,
                                    selected_option=selected_option
                                )
                                logger.debug(f"Saved selected option for Question {question.id}: {selected_option.text}")

                # Display a success message
                survey_type = "republished" if survey.status == 'republished' else "published"
                messages.success(request, f"Your response to the {survey_type} survey '{survey.name}' has been submitted successfully!")
                return redirect('completion_message')

        except Exception as e:
            # Log any unexpected errors for debugging
            logger.error(f"Error during survey submission: {e}", exc_info=True)
            messages.error(request, "An error occurred while submitting your response. Please try again.")
            return redirect('taker_dashboard')

    # Redirect to the taker dashboard if the request method is not POST
    messages.error(request, "Invalid request method.")
    return redirect('taker_dashboard')




# Publish Survey
def publish_survey(request, survey_id):
    """Publish a survey."""
    if not request.user.is_authenticated or not request.user.is_staff:
        messages.error(request, "Access denied!")
        return redirect('login')

    try:
        survey = Survey.objects.get(id=survey_id, creator=request.user, is_deleted=False)
        if survey.status == Survey.DRAFT:
            survey.status = Survey.PUBLISHED
            survey.save()
            messages.success(request, f"Survey '{survey.name}' has been published!")
        else:
            messages.warning(request, f"Survey '{survey.name}' is already published or closed.")
    except Survey.DoesNotExist:
        messages.error(request, "Survey not found or you don't have permission to access it.")

    return redirect('creator_dashboard')

def republish_survey(request, survey_id):
    """Republish a survey to allow new responses and display aggregated results."""
    if not request.user.is_authenticated or not request.user.is_staff:
        messages.error(request, "Access denied! You need to log in with a staff account.")
        return redirect('login')

    # Fetch the survey and ensure it exists
    survey = get_object_or_404(Survey, id=survey_id, creator=request.user, is_deleted=False)

    # Check the current status of the survey
    if survey.status == 'published':
        survey.status = 'republished'  # Change to the "republished" state
        survey.save()
        messages.success(request, f"Survey '{survey.name}' has been republished successfully! Now users can submit responses.")
    elif survey.status == 'republished':
        messages.info(request, f"Survey '{survey.name}' is already republished.")
    else:
        # If the survey is not in the correct state, warn the user
        messages.warning(request, f"Survey '{survey.name}' cannot be republished because it is in the '{survey.status}' state.")

    # Redirect to the creator dashboard
    return redirect('creator_dashboard')


def view_results(request, survey_id):
    """Display the final results of a closed survey."""
    survey = get_object_or_404(Survey, id=survey_id, is_deleted=False)
    
    # Ensure the survey is closed
    if survey.status != 'closed':
        messages.error(request, "This survey is not closed yet.")
        return redirect('creator_dashboard')
    
    results = []  # To store the results for display
    
    # Loop through each question and aggregate the results
    for question in survey.questions.filter(is_deleted=False):
        question_data = {
            'text': question.text,
            'options': []
        }
        total_responses = sum(option.answers.count() for option in question.options.all())
        
        for option in question.options.all():
            selected_count = option.answers.count()
            percentage = (selected_count / total_responses * 100) if total_responses > 0 else 0
            question_data['options'].append({
                'text': option.text,
                'count': selected_count,
                'percentage': round(percentage, 2)
            })
        
        results.append(question_data)
    
    return render(request, 'surveys/view_results.html', {
        'survey': survey,
        'results': results,
        'page_title': f"Results for Survey: {survey.name}",
    })





def survey_response_table(request, survey_id):
    """Display the survey responses table with response counts and percentages for each option."""
    # Get the survey object by id
    survey = get_object_or_404(Survey, id=survey_id)

    # Get all questions for the survey
    questions = survey.questions.filter(is_deleted=False)

    # Initialize the results array
    results = []

    # Loop through each question to gather response data
    for question in questions:
        question_data = {
            "text": question.text,
            "options": [],
        }

        # Get all options for the question
        options = question.options.all()

        # Get total responses for this question (count of answers)
        total_responses = Answer.objects.filter(question=question).count()

        for option in options:
            # Get the response count for each option
            response_count = Answer.objects.filter(selected_option=option).count()

            # Calculate percentage for the option
            percentage = (response_count / total_responses * 100) if total_responses > 0 else 0

            # Append option data to the question's options list
            question_data["options"].append({
                "text": option.text,
                "response_count": response_count,
                "percentage": round(percentage, 2)  # Round percentage to 2 decimal places
            })

        # Append question data to the results array
        results.append(question_data)

    # Pass the results and survey data to the template
    return render(request, 'surveys/survey_response_table.html', {
        'page_title': f"Survey Responses: {survey.name}",
        'survey': survey,
        'results': results,
    })