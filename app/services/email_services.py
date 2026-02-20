from pydantic import EmailStr
import resend, os

from app.core.utils import load_enviroment_variables

load_enviroment_variables()

resend.api_key = os.getenv("RESEND_API_KEY")


class EmailServices:
    @classmethod
    def send_mail(
        cls,
        *,
        to: EmailStr,
        body: str | None = None,
        subject: str,
        html: str | None = None,
    ) -> resend.Emails.SendResponse | None:
        params: resend.Emails.SendParams = {
            "from": "Chuks Kitchen <chuckskitchen@resend.dev>",
            "to": [to],
            "subject": subject,
        }
        if body:
            params["text"] = body
        elif html:
            params["html"] = html
        try:
            email: resend.Emails.SendResponse = resend.Emails.send(params)
            return email
        except Exception as e:
            print(f"unable to send email due to {e}")

    @classmethod
    def send_otp_mail(cls, *, to: EmailStr, otp: str | int):
        return cls.send_mail(
            to=to,
            subject="Chuks - Verify your email address",
            body=f"Your OTP is {otp}",
        )
