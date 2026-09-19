import smtplib

from app.core.celery_app import celery_app
from app.services.email_service import (
    send_task_assignment_email,
)

@celery_app.task(
    bind=True,
    autoretry_for=(
        OSError,
        smtplib.SMTPException,
    ),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_kwargs={"max_retries": 3},
)
def send_task_assignment_email_task(
        self,
        to_email: str,
        recipient_name: str,
        task_id: int,
        task_title: str,

        
) -> None:
    send_task_assignment_email(
        to_email=to_email,
        recipient_name=recipient_name,
        task_id=task_id,
        task_title=task_title,
    )
