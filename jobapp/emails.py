import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def _send(subject, message, recipient):
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [recipient])
    except Exception:
        logger.exception('Could not send email to %s', recipient)


def send_status_email(application):
    candidate = application.candidate
    if not candidate.email:
        return
    subject = f'Update on your application for {application.job.title}'
    message = (
        f'Hi {candidate.get_full_name() or candidate.username},\n\n'
        f'Your application for "{application.job.title}" at '
        f'{application.job.company_name} is now: '
        f'{application.get_status_display()}.\n\n'
        f'Log in to JobPortal to see the details.\n\n'
        f'- JobPortal'
    )
    _send(subject, message, candidate.email)


def send_new_application_email(application):
    recruiter = application.job.recruiter
    if not recruiter.email:
        return
    subject = f'New application for {application.job.title}'
    message = (
        f'Hi {recruiter.get_full_name() or recruiter.username},\n\n'
        f'{application.candidate.get_full_name() or application.candidate.username} '
        f'applied for "{application.job.title}".\n\n'
        f'Log in to JobPortal to review the application.\n\n'
        f'- JobPortal'
    )
    _send(subject, message, recruiter.email)