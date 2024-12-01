from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.middleware.csrf import get_token  # CSRF token debugging
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
    if not request.user.is_authenticated or not request.user.is_staff:
        messages.error(request, "Access denied!")
        return redirect('taker_dashboard' if not request.user.is_staff else 'login')

    drafts = Survey.objects.filter(creator=request.user, status='draft', is_deleted=False)
    published = Survey.objects.filter(creator=request.user, status='published', is_deleted=False)
    closed = Survey.objects.filter(creator=request.user, status='closed', is_deleted=False)

    return render(request, 'surveys/creator_dashboard.html', {
        'page_title': 'Creator Dashboard',
        'drafts': drafts,
        'published': published,
        'closed': closed,
    })


# Taker Dashboard
def taker_dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.user.is_staff:
        return redirect('creator_dashboard')

    # Retrieve published surveys for the taker
    surveys = Survey.objects.filter(status='published', is_deleted=False)
    return render(request, 'surveys/taker_dashboard.html', {
        'page_title': 'Taker Dashboard',
        'surveys': surveys,
    })


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





# Edit Survey
def edit_survey(request, survey_id):
    """Allow creators to edit existing surveys."""
    if not request.user.is_authenticated or not request.user.is_staff:
        messages.error(request, "Access denied!")
        return redirect('login')

    survey = get_object_or_404(Survey, id=survey_id, creator=request.user, is_deleted=False)
    if request.method == "POST":
        survey.name = request.POST.get('survey_name', survey.name)
        survey.description = request.POST.get('description', survey.description)
        survey.status = request.POST.get('status', survey.status)
        survey.save()
        messages.success(request, f"Survey '{survey.name}' updated successfully!")
        return redirect('creator_dashboard')

    return render(request, 'surveys/edit_survey.html', {'page_title': 'Edit Survey', 'survey': survey})


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
    """Allow a user to take a specific survey."""
    if not request.user.is_authenticated:
        return redirect('login')

    # Get the survey and its related questions
    survey = get_object_or_404(Survey, id=survey_id, status='published', is_deleted=False)
    questions = survey.questions.filter(is_deleted=False)  # Fetch related questions

    if request.method == 'POST':
        # Placeholder for processing survey responses (you can expand this later)
        messages.success(request, f"Your response to survey '{survey.name}' has been submitted successfully!")
        return redirect('completion_message')

    # Pass the survey and questions to the template
    return render(request, 'surveys/take_survey.html', {
        'page_title': f"Take Survey: {survey.name}",
        'survey': survey,
        'questions': questions,  # Pass questions to the template
    })


# Completion Message
def completion_message(request):
    """Display a completion message after survey submission."""
    return render(request, 'completion_message.html', {'page_title': 'Thank You'})


# Survey Results
def survey_results(request, survey_id):
    """Display the results of a specific survey."""
    if not request.user.is_authenticated:
        return redirect('login')
    if not request.user.is_staff:
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
    """Handle survey submission."""
    if not request.user.is_authenticated:
        messages.error(request, "You must be logged in to submit a survey.")
        return redirect('login')

    survey = get_object_or_404(Survey, id=survey_id, status='published', is_deleted=False)

    if request.method == "POST":
        # Create a response for the user and survey
        response = response.objects.create(
            survey=survey,
            taker=request.user
        )

        for key, value in request.POST.items():
            if key.startswith('question_'):  # Matches the format in the take_survey.html
                question_id = key.split('_')[1]
                question = get_object_or_404(question, id=question_id, survey=survey)

                # Determine if the answer is for text input or a selected option
                if question.question_type == 'text':
                    # Save text response
                    answers.objects.create(
                        response=response,
                        question=question,
                        text=value
                    )
                elif question.question_type in ['multiple_choice', 'checkbox']:
                    # Save selected option response
                    option = get_object_or_404(option, id=value, question=question)
                    Answer.objects.create(
                        response=response,
                        question=question,
                        selected_option=option
                    )

        messages.success(request, f"Thank you for completing the survey '{survey.name}'!")
        return redirect('taker_dashboard')

    messages.error(request, "Invalid submission method.")
    return redirect('taker_dashboard')
