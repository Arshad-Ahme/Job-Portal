# JobPortal
 
A full-stack job search and recruitment web application built with Django and Bootstrap 5. Recruiters post and manage jobs and review applicants. Candidates search jobs, apply with a resume, save jobs, and track their application status.
 
**Live demo:** <add link after deployment>
 
## Features
 
**Candidates**
- Sign up, log in, and reset a forgotten password by email
- Search jobs by keyword, location, category, job type, and experience level, with pagination
- Apply with a resume (PDF or Word, up to 2 MB) and a cover letter
- Track the status of each application: applied, shortlisted, rejected, hired
- Save and unsave jobs
- Edit profile (phone, skills, bio, resume)
 
**Recruiters**
- Post, edit, close, and reopen jobs
- See the number of applicants per job and review each applicant's details and resume
- Change the application status, which emails the candidate
- Receive an email when a candidate applies
- Edit company profile (website, description, logo)
 
**General**
- Role-based access control (candidate and recruiter) with a custom user model
- Validation for deadlines, salary range, resume type and size
- Responsive interface built with Bootstrap 5
- Automated test suite
 
## Tech stack
 
Python, Django, Django ORM, HTML, CSS, Bootstrap 5, JavaScript, SQLite, django-crispy-forms, Pillow, Faker, Git
 
## Screenshots
 
| Home | Job list |
|---|---|
|
 
![Home](docs/screenshots/home.png)
 
|
 
![Job list](docs/screenshots/job-list.png)
 
|
 
| Job detail | Recruiter dashboard |
|---|---|
|
 
![Job detail](docs/screenshots/job-detail.png)
 
|
 
![Recruiter](docs/screenshots/recruiter.png)
 
|
 
| Applicants | My applications |
|---|---|
|
 
![Applicants](docs/screenshots/applicants.png)
 
|
 
![Applications](docs/screenshots/applications.png)
 
|
 
## Project structure
 
```
Job-Portal/
├── accounts/        custom user, signup, login, profiles, password reset
├── jobapp/          jobs, applications, saved jobs, emails, seed command
├── JobPortal/       project settings and root URLs
├── templates/       base layout and all pages
├── static/css/      custom styles
├── manage.py
└── requirements.txt
```
 
## Getting started
 
Requires Python 3.12 or newer.
 
```bash
git clone <your-repository-url>
cd Job-Portal
 
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux
 
pip install -r requirements.txt
```
 
Create a `.env` file next to `manage.py`:
 
```
SECRET_KEY='your-secret-key'
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
CSRF_TRUSTED_ORIGINS=http://127.0.0.1:8000,http://localhost:8000
```
 
Then:
 
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_data --jobs 100
python manage.py runserver
```
 
Open http://127.0.0.1:8000/
 
## Demo accounts
 
After running `seed_data`, log in with password `Demo@12345`:
 
| Role | Username |
|---|---|
| Recruiter | `demo_recruiter1` |
| Candidate | `demo_candidate1` |
 
In development, emails (status updates, password reset) are printed in the terminal.
 
## Running tests
 
```bash
python manage.py test
```
 
## What I learned
 
- Designing relational models with a custom user model and role-based permissions
- Handling file uploads securely with validation
- Writing views that protect data so users can only change their own records
- Writing automated tests for permissions and workflows
 
## Roadmap
 
- [ ] PostgreSQL
- [ ] Docker
- [ ] Deployment
- [ ] REST API with Django REST Framework
