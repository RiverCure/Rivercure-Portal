from dotenv import load_dotenv
from celery import shared_task

from django.core.mail import send_mail

from .models import e_ContextContribution

import os
import requests

load_dotenv()


# Use Exponential Backoff and retry a maximum of 5 times
# As seen in: https://testdriven.io/blog/retrying-failed-celery-tasks/
@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 5})
def lat_long_to_address(self, contribution_id):

    contribution = e_ContextContribution.objects.get(id=contribution_id)

    if contribution:
        lat = contribution.get_lat()
        long = contribution.get_long()

        # Call API
        # We are using LocationIQ API
        # TODO: Make sure we are following all the directives of the free plan
        api_url = "https://eu1.locationiq.com/v1/reverse?key={}&lat={}&lon={}&format=json&".format(os.getenv('REVGEO_API_KEY', ''), lat, long)
        headers = {"accept": "application/json"}

        response = requests.get(api_url, headers, timeout=10.0)

        if response.status_code == 200:
            # Request went well, we can save the address
            response_parsed = response.json()
            address = response_parsed['display_name']
            contribution.observationAddress = address
            contribution.save()
        else:
            # Oops, something went wrong
            print("Reverse Geocoding API Error:", response.status_code, response.text)
            raise Exception()


@shared_task(bind=True)
def send_contribution_submit_confirmation(self, contribution):

    try:
        send_mail(
            subject=f'Contribution {contribution.id} submitted successfully!',
            message=f'Your Contribution {contribution.id} has been successfully submitted to Context {contribution.context.Name}. You will be notified once it has been accepted or rejected.',
            from_email=None, # TODO: Is this working?
            recipient_list=contribution.createdBy.email,
        )
    except:
        raise Exception("Error sending email")