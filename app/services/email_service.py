import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger(__name__)

def send_email(
        to_email: str,
        subject: str,
        body: str,
) -> None:
    if not settings.email_enabled:
        logger.info(
            "Email skipped because email is disabled: to=%s subject=%s",
            to_email,
            subject,
        )
        return

    if (
        settings.smtp_host is None
        or settings.smtp_username is None
        or settings.smtp_username is None
        or settings.smtp_password is None
        or settings.smtp_from_email is None
    ):
        logger.error(
            "Email is enabled but SMTP configuration is incomplete."
        )
        return

    message = EmailMessage()

    message["From"] = settings.smtp_from_email
    message["To"] = to_email
    message["subject"] = subject

    message.set_content(body)

    try:
        with smtplib.SMTP(
            settings.smtp_host,
            settings.smtp_port,
            timeout=10,
        ) as smtp:
            smtp.starttls()

            smtp.login(
                settings.smtp_username,
                settings.smtp_password,
            )

            smtp.send_message(message)

        logger.info(
            "Email sent: to=%s subject=%s",
            to_email,
            subject,
        )

    except (OSError, smtplib.SMTPException):
        logger.exception(
            "Failed to send email: to=%s subject=%s",
            to_email,
            subject,
        )
        raise

def send_task_assignment_email(
        to_email: str,
        recipient_name: str,
        task_id: int,
        task_title: str,
) -> None:
    subject = f"You were assigned a task: {task_title}"

    body = f"""
Hello {recipient_name},

You have been assigned a new task.

Task ID: {task_id}
Task title: {task_title}

Log in to Task Assignment API to view the task details.

Regards,
Task Management API
""".strip()

    send_email(
        to_email=to_email,
        subject=subject,
        body=body,
    )

