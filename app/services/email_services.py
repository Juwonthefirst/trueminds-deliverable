from pydantic import EmailStr
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.core.utils import load_enviroment_variables

load_enviroment_variables()


class EmailServices:
    @classmethod
    def send_mail(
        cls,
        *,
        to: EmailStr,
        body: str | None = None,
        subject: str,
        html: str | None = None,
    ) -> bool:
        sender_email = os.getenv("SMTP_EMAIL")
        sender_password = os.getenv("SMTP_PASSWORD")
        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))

        if not sender_email or not sender_password:
            print("SMTP credentials not configured")
            return False

        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = sender_email
            message["To"] = to

            if html:
                message.attach(MIMEText(html, "html"))
            elif body:
                message.attach(MIMEText(body, "plain"))

            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, [to], message.as_string())

            return True
        except Exception as e:
            print(f"unable to send email due to {e}")
            return False

    @classmethod
    def send_otp_mail(cls, *, to: EmailStr, otp: str | int):
        return cls.send_mail(
            to=to,
            subject="Chuks - Verify your email address",
            body=f"Your OTP is {otp}",
        )
