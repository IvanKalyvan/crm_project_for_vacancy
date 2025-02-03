import socket

from time import sleep
from django.core.mail import send_mail
from celery import shared_task
from django.conf import settings

def is_internet_available(host="8.8.8.8", port=53, timeout=3):

    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error:
        return False

@shared_task(bind=True)
def send_confirmation_email(self, email, subject, message):

    while True:
        if is_internet_available():
            try:
                send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        email,
                        fail_silently=False,
                    )
                break
            except Exception:
                sleep(5)
        else:
            sleep(5)
