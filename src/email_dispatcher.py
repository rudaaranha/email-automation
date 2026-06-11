"""Handles email sending via Gmail SMTP server.
    
    This class is responsible for establishing the SMTP connection,
    creating email messages, and sending them to recipients.
    It supports test mode where emails are simulated without actual sending.
"""

import smtplib
from email.message import EmailMessage
from typing import Optional
from src.config import Config
from src.email_templates import EmailTemplates


class EmailDispatcher():
    

    def __init__(self, config: Config = None):
        """Initialize the email dispatcher with configuration.
        
        Args:
            config: Configuration object. If None, creates a new Config instance.
        """
        self.config = config or Config()

        # email credentials
        self.email = self.config.EMAIL_NATS
        self.password = self.config.SENHA_APP_NATS

        # SMTP server configuration
        self.smtp_server = self.config.SMTP_SERVER
        self.smtp_port = self.config.SMTP_PORT

        # email templates instance
        self.templates = EmailTemplates()

        # Test mode flag
        self.test_mode = self.config.TEST_MODE

    def _send(self, to_email: str, subject: str, html_body: str) -> bool:
        """
        Private method that actually sends the email via SMTP.
        
        Args:
            to_email: Recipient email address
            subject: Email subject line
            html_body: HTML content of the email
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        # Test mode: simulate sending without actually connecting to SMTP
        if self.test_mode:
            print(f"\n [TEST MODE] Would send email to: {to_email}")
            print(f"   Subject: {subject}")
            print(f"   Body preview: {html_body}...")
            return True

        # Production mode: actually send the email
        try:
            # Create email message
            msg = EmailMessage()
            msg['From'] = self.email
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.set_content(html_body, subtype='html')

            # Connect to gmail SMTP server and send
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email, self.password)
                server.send_message(msg)

            print(f"Email sent successfully to: {to_email}")
            return True
        
        except smtplib.SMTPAuthenticationError:
            print(f"Authentication failed. Check your email and app password.")
            return False
        except smtplib.SMTPException as e:
            print(f"SMTP error: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error: {e}")
            return False

    
    def send_alert_start(self, to_email: str, responsible_name: str, activity_name: str,
                         start_date: str, end_date: str, project_name: str) -> bool:
        """
        Send a "start activity" alert email.
        
        Args:
            to_email: Recipient email address
            responsible_name: Name of the responsible person
            activity_name: Name of the activity
            start_date: Formatted start date (DD/MM/YYYY)
            end_date: Formatted end date (DD/MM/YYYY)
            project_name: Name of the project
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        subject = f"[ALERT] Start Activity: {activity_name} - {project_name}"

        html_body = self.templates.alert_start(
            responsible_name=responsible_name,
            activity_name=activity_name,
            start_date=start_date,
            end_date=end_date,
            project_name=project_name
        )

        return self._send(to_email, subject, html_body)


    def send_alert_delay(self, to_email: str, responsible_name: str, activity_name: str,
                         end_date: str, days_delayed: int, project_name: str) -> bool:
        """
        Send a "delayed activity" alert email.
        
        Args:
            to_email: Recipient email address
            responsible_name: Name of the responsible person
            activity_name: Name of the activity
            end_date: Formatted end date (DD/MM/YYYY)
            days_delayed: Number of days the activity is delayed
            project_name: Name of the project
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        subject = f"[URGENT] Delayed Activity: {activity_name} - {project_name}"

        html_body = self.templates.alert_delay(
            responsible_name=responsible_name,
            activity_name=activity_name,
            end_date=end_date,
            days_delayed=days_delayed,
            project_name=project_name
        )
        return self._send(to_email, subject, html_body)


    def send_alert_completion(self, to_email: str, responsible_name: str,
                              activity_name: str, project_name: str) -> bool:
        """
        Send a "activity completed" alert email.
        
        Args:
            to_email: Recipient email address
            responsible_name: Name of the responsible person
            activity_name: Name of the activity
            project_name: Name of the project
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        subject = f"[CONGRATULATIONS] Activity Completed: {activity_name} - {project_name}"
        
        html_body = self.templates.alert_completion(
            responsible_name=responsible_name,
            activity_name=activity_name,
            project_name=project_name
        )
        
        return self._send(to_email, subject, html_body)
    

    def send_daily_report(self, to_email: str, activities_to_start: list,
                          activities_delayed: list, project_name: str) -> bool:
        """
        Send a daily report email with summary of activities.
        
        Args:
            to_email: Recipient email address (usually coordinator)
            activities_to_start: List of activities that start today
            activities_delayed: List of delayed activities
            project_name: Name of the project
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        subject = f"[DAILY REPORT] Activities Summary - {project_name}"
        
        html_body = self.templates.daily_report(
            activities_to_start=activities_to_start,
            activities_delayed=activities_delayed,
            project_name=project_name
        )
        
        return self._send(to_email, subject, html_body)
