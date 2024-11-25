from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .forms import SurveyForm, QuestionForm, OptionForm  # Import forms
from .models import Survey, Question, Option, Response  # Import models

# Homepage View
def homepage(request):
    return render(request, 'Survey/1_homepage.html')

# Registration View
def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        role = request.POST['role']

        try:
            user = User.objects.create_user(username=username, password=password)
            user.save()
            return redirect('login')
        except Exception:
            return render(request, 'Survey/2_register.html', {'error': 'User already exists'})

    return render(request, 'Survey/2_register.html')

# Login View
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            if user.is_superuser:
                return redirect('creator_dashboard')
            else:
                return redirect('taker_dashboard')
        else:
            return render(request, 'Survey/3_login.html', {'error': 'Invalid username or password'})
    return render(request, 'Survey/3_login.html')

# Creator Dashboard View
@login_required
def creator_dashboard(request):
    return render(request, 'Survey/4_creator_dashboard.html')

# Taker Dashboard View
@login_required
def taker_dashboard(request):
    return render(request, 'Survey/8_taker_dashboard.html')


# Survey Creation View
@login_required
def create_survey(request):
    if request.method == 'POST':
        survey_form = SurveyForm(request.POST)
        question_texts = request.POST.getlist('question_text')
        question_types = request.POST.getlist('question_type')
        options_list = request.POST.getlist('options')

        if survey_form.is_valid():
            survey = survey_form.save(commit=False)
            survey.creator = request.user
            survey.save()

            for text, q_type, opts in zip(question_texts, question_types, options_list):
                question = Question.objects.create(
                    survey=survey,
                    text=text,
                    question_type=q_type
                )
                for opt in opts.split(','):
                    Option.objects.create(question=question, text=opt.strip())

            return redirect('creator_dashboard')

    return render(request, 'Survey/5_create_survey.html', {'form': SurveyForm()})

# Add Option View
@login_required
def add_option(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    
    if request.method == 'POST':
        option_text = request.POST.get('option_text')
        if option_text:
            Option.objects.create(question=question, text=option_text.strip())
            return redirect('edit_survey', survey_id=question.survey.id)

    return render(request, 'Survey/add_option.html', {'question': question})


@login_required
def manage_surveys(request):
    surveys = Survey.objects.filter(creator=request.user)  # Fetch surveys created by the logged-in user
    return render(request, 'Survey/7_manage_surveys.html', {'surveys': surveys})


# Survey Editing View
@login_required
def edit_survey(request, survey_id):
    survey = get_object_or_404(Survey, id=survey_id, creator=request.user)
    questions = Question.objects.filter(survey=survey)

    if request.method == 'POST':
        survey_form = SurveyForm(request.POST, instance=survey)
        if survey_form.is_valid():
            survey_form.save()

            question_ids = request.POST.getlist('question_id')
            question_texts = request.POST.getlist('question_text')
            question_types = request.POST.getlist('question_type')
            options_lists = request.POST.getlist('options')

            for question_id, text, q_type, opts in zip(question_ids, question_texts, question_types, options_lists):
                if question_id:
                    question = get_object_or_404(Question, id=question_id, survey=survey)
                    question.text = text
                    question.question_type = q_type
                    question.save()
                else:
                    question = Question.objects.create(
                        survey=survey,
                        text=text,
                        question_type=q_type
                    )

                existing_options = Option.objects.filter(question=question)
                existing_options.delete()
                for opt in opts.split(','):
                    Option.objects.create(question=question, text=opt.strip())

            return redirect('manage_surveys')

    survey_form = SurveyForm(instance=survey)
    return render(
        request,
        'Survey/6_edit_survey.html',
        {'form': survey_form, 'survey': survey, 'questions': questions}
    )

# View to take a survey
@login_required
def take_survey(request, survey_id):
    survey = get_object_or_404(Survey, id=survey_id)
    questions = Question.objects.filter(survey=survey)

    if request.method == 'POST':
        for question in questions:
            selected_option_id = request.POST.get(f'question_{question.id}')
            if selected_option_id:
                selected_option = get_object_or_404(Option, id=selected_option_id)
                Response.objects.create(
                    question=question,
                    user=request.user,
                    selected_option=selected_option
                )
        return redirect('survey_list')

    return render(request, 'Survey/10_take_survey.html', {'survey': survey, 'questions': questions})


# View to list published surveys for survey takers
@login_required
def survey_list(request):
    surveys = Survey.objects.filter(status='Published')  # Fetch published surveys
    return render(request, 'Survey/9_survey_list.html', {'surveys': surveys})


# View to display survey results
@login_required
def survey_results(request, survey_id):
    survey = get_object_or_404(Survey, id=survey_id)
    questions = Question.objects.filter(survey=survey)

    results = []
    for question in questions:
        options = Option.objects.filter(question=question)
        option_results = [
            {
                'option': option,
                'count': Response.objects.filter(selected_option=option).count()
            }
            for option in options
        ]
        results.append({'question': question, 'options': option_results})

    return render(request, 'Survey/11_survey_results.html', {'survey': survey, 'results': results})


# Completion Message View
@login_required
def completion_message(request):
    return render(request, 'Survey/12_completion_message.html')  # Render the completion confirmation page

@login_required
def logout_view(request):
    logout(request)
    return redirect('homepage')  # Redirect to homepage after logout
