***SURVEY MASTER***
SurveyMaster is a Django-based web application that will help the users to create, edit, manage and take part in the surveys. The application will accomodate 2 types of users,Survey Creators and Survey Takers. Creators can basically create and edit the surveys with multiple questions each having multiple choices of answer. 
Survey Takers will have the opportunity to take part in the survey, answer the survey with the choies provided.


-----------------------------------------


Table of Contents
- [Features]
- [Getting Started]
- [Usage Instructions]
- [Limitations]


-----------------------------------------


FEATURES:
User registration and login page, will help the user to create a user and login to access the features

Role-Based Dashboards:
Survey Creators: Manage the surveys by creating, editing, publishing and closing the survey.
Survey Takers: Will be able to view only the available surveys that were published and take the survey and submit it. The user will also be able take the republished survey which will give them the insights of previous taken user's opinion/option chosen on that survey (Which is "Wisdom of Crowd").

Survey Results:
Results that were cumulated for the creators/admins to view. And There will be a survey completed confirmation for the survey takers.

Survey Management:
Create MCQ's and save surveys as drafts and publish them for the survey takers to take the surveys.

Admin Panel:
An admin panel to manage all the users and the surveys.


-----------------------------------------


GETTING STARTED
Follow the below steps to run this project on your local machine.

PREREQUISITES:
Python 3.11+
PostgreSQl (or SQLite)


INSTALLATION:
1)Clone the repository:
   ```bash
   git clone https://github.com/YourGitHubUsername/SurveyMaster.git
   cd SurveyMaster

2)Install dependencies
    pip install -r requirements.txt

3)Setup the database
    Create a database with your desired name
    Add that database name and your credentials in settings.py

4)Migrate
    python manage.py makemigrations
    python manage.py migrate

4.1)Collectstatic
    python manage.py collectstatic

5)Create a superuser
    python manage.py createsuperuser
    it will ask for a username, email address, password and make sure the password is a little different from the above details.

6)Run the server
    python manage.py runserver
    Access the application at http://127.0.0.1:8000/ in your web browser


-----------------------------------------


USAGE INSTRUCTIONS:

1)LOGIN: 
Use the superuser credentials (python manage.py createsuperuser) using the command prompt to log in to the admin dashboard.
In our project, we tested the application using these credentials:

[ ADMIN:
Username: AdminTestUser
Email: admintestuser@gmail.com
Password: Testing@1

SURVEY TAKER:
Username: User1
Email: user1@gmail.com
Password: Testing@User1

Username: User2
Email: User2@gmail.com
Password: Testing@User2 ]

TO access the survey takers dashboard, register as a new user in the web interface and log in with that credentials.

2)Survey Creator:
Login with the superuser credential and access the creator dashboard
Create surveys with a name, description and question with the answer.
Save surveys as draft and publish them for the survey takers to access them.
View and manage the responses to the surveys, and can republish the surveys.

3)Survey Taker:
Access the survey taken dashboard after succesfully logging in with the credentials.
View all the available surveys that the user can take.
Answer the surveys by choosing the appropriate answer.
view the aggregated results for the republished surveys for insights and retake them if you have had a change of mind.

4)Admin Panel:
Superusers can access the admin panel and manage users, surveys and responses from the users directly from the admin interface

5) Create Survey Option types
In the Edit Survey Page for the questions type you can see options like "Checkbox (Multiple Choice)", "Text Response", and "Radio Button (Single Choice)"
As per the requirement document we have added the backend logic only for the Mulitple Choice type which is "Radio Button (Single Choice)". And for others options they are dispyed as dummy types. 


-----------------------------------------


LIMITATIONS:

Pagination: Survey results page lacks pagination for large datasets.

Email Notifications: No email notification system for user registration or password recovery.

UI/UX: The interface can be enhanced for better usability.


