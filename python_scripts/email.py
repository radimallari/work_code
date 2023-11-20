import datetime as dt
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import NamedTuple, Optional

from trapy.util import log
from trapy.util.excel import Traveler
from trapy.util.iter import lines

TIMESTAMP_FMT = "%a %H:%M %m-%d-%Y"
M_SPACE = "&emsp;"

logger = log.getLogger(__name__)


def notify(function):
    notification_email = "0df456fc.wyatt.com@amer.teams.ms"

    def notify_wrp(*args, **kwargs):
        try:
            traveler = Traveler()
            serial_number = traveler.serialNumber
            tn_rma_number = traveler.RMANumber or traveler.trackingNumber
            message = MIMEMultipart("alternative")

            timestamp = dt.datetime.strftime(dt.datetime.now(), TIMESTAMP_FMT)
            message[
                "Subject"
            ] = f"{timestamp} Running: {function.__module__}.{function.__name__} {serial_number}"
            message["To"] = notification_email

            traveler_location = f"<a>{log.WB_PATH}</a>" if log.WB_PATH else "Not Found"

            html = lines(
                "<html>",
                "    <body>",
                "        <p>",
                "        <b>Computer/User Name</b>:",
                f"        {os.environ['COMPUTERNAME']}/{os.getlogin()}",
                f"        <br><b>SN/TN or RMA:</b>",
                f"        {serial_number}/{tn_rma_number}",
                f"        <br>{traveler_location}",
                "        </p>",
                "    </body>",
                "</html>",
            )
            message.attach(MIMEText(html, "html"))
            send_email(message, notification_email)
        except Exception:
            logger.exception("Failed to construct/send email notification.")
        logger.debug("Sending notification email")
        return function(*args, **kwargs)

    return notify_wrp


class ErrorReport(NamedTuple):
    error_msg: str
    user_log_in: str
    computer_name: str
    teams_email: Optional[str] = None
    tech_name: Optional[str] = None
    inst_serial_number: Optional[str] = None
    inst_tn_rma_number: Optional[str] = None
    contact_method: Optional[str] = None
    additional_info: Optional[str] = None


def autoMailError(error_data: ErrorReport, reported_error: bool = False):
    """Mails trapy error to a Traveler Support Teams channel.

    :param error_data: Named tuple containing various data of error.
    :param reported_error: Flag for to construct additional information provided by
    the user.
    :return:
    """

    message = MIMEMultipart("alternative")
    try:
        last_line_of_error = error_data.error_msg.strip("\n").rsplit("\n", 1)[-1]
    except Exception:
        last_line_of_error = ""
    subject_text = last_line_of_error or error_data.additional_info
    timestamp = dt.datetime.strftime(dt.datetime.now(), TIMESTAMP_FMT)
    message["Subject"] = f"{timestamp} {subject_text}"
    message["To"] = f"<{error_data.teams_email}>"
    error_msg_html = error_data.error_msg.replace("\n", "<br>").replace(
        " " * 4, M_SPACE
    )
    traveler_location = f"<a>{log.WB_PATH}</a>" if log.WB_PATH else "Not Found"
    reported_string = ""
    if reported_error:
        reported_string = f"""
                <br><b>Technician Name & Report:</b>
                {error_data.tech_name} - {error_data.additional_info}
                <br><b>SN/TN or RMA:</b>
                {error_data.inst_serial_number}/{error_data.inst_tn_rma_number}
                <br><b>Preffered Contact:</b> {error_data.contact_method}
                """
    html = f"""
                <html>
                    <body>
                        <p>
                        <b>Computer/User Name</b>:
                        {error_data.computer_name}/{error_data.user_log_in}
                        {reported_string}
                        <br>{traveler_location}
                        <br>{error_msg_html}
                        </p>
                    </body>
                </html>
                """
    message.attach(MIMEText(html, "html"))
    send_email(message, error_data.teams_email)


def send_email(email_message, email_to):
    traveler_support_email = "travelersupport@wyatt.com"
    traveler_support_pw = "Rosemark543!"
    email_message["From"] = traveler_support_email
    with smtplib.SMTP(host="smtp.office365.com", port=587) as server:
        server.ehlo()
        server.starttls()
        server.login(traveler_support_email, traveler_support_pw)
        server.sendmail(traveler_support_email, email_to, email_message.as_string())
