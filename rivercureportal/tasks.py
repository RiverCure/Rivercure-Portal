from celery import shared_task

from django.core.mail import send_mail

@shared_task(bind=True)
def send_contact_email(self, contact):
    try:
        send_mail(
            subject=contact['subject'],
            message=contact['message'],
            from_email=contact['from_email'],
            recipient_list=['to@email.com'],  #TODO: Put the real one
        )
    except:
        raise Exception("Error sending Contact email")