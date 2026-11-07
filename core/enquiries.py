"""Emails for contact form submissions, sent with the SMTP details in EmailSettings.

Callers save the submission first, so an enquiry survives a mail failure.
"""
import logging
from html import unescape

from django import forms
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags
from wagtail.rich_text import expand_db_html

from .models import EmailSettings, SiteSettings

logger = logging.getLogger(__name__)

# Also hard-coded in templates/includes/enquiry_form.html. Named so that it cannot collide with
# a field an editor adds in the form builder, which would silently drop real enquiries.
HONEYPOT_FIELD = "contact_website"


def is_spam(request):
    return bool(request.POST.get(HONEYPOT_FIELD))


def _rows(form):
    """The submitted answers as (label, value) pairs, in form order."""
    rows = []
    for name, field in form.fields.items():
        value = form.cleaned_data.get(name)
        if isinstance(value, (list, tuple)):
            value = ", ".join(str(item) for item in value)
        rows.append((str(field.label), "" if value in (None, "") else str(value)))
    return rows


def _visitor_email(form):
    for name, field in form.fields.items():
        if isinstance(field, forms.EmailField) and form.cleaned_data.get(name):
            return form.cleaned_data[name]
    return ""


def _visitor_name(form):
    for name in form.fields:
        if "name" in name and not any(word in name for word in ("company", "organisation")):
            # Collapsed to one line because it is used in the subject header.
            return " ".join(str(form.cleaned_data.get(name) or "").split())[:78]
    return ""


def _greeting_name(visitor_name):
    """A first name for the confirmation, or nothing if it looks like a link or an address."""
    first = visitor_name.split()[0][:40] if visitor_name else ""
    return "" if any(character in first for character in "./:@") else first


def _send(subject, text, html, email_settings, connection, to, cc=None, reply_to=None):
    message = EmailMultiAlternatives(
        subject=subject,
        body=text,
        from_email=email_settings.sender,
        to=to,
        cc=cc,
        reply_to=reply_to,
        connection=connection,
    )
    message.attach_alternative(html, "text/html")
    message.send(fail_silently=False)


def send_enquiry_emails(page, form):
    """Notify the team and, if enabled, confirm to the visitor.

    Returns False when email is not configured. Raises if the notification cannot be sent;
    a failed confirmation is only logged because the team already has the enquiry.
    """
    email_settings = EmailSettings.for_site(page.get_site())
    if not email_settings.is_configured:
        logger.warning("Enquiry saved but not emailed: Email Settings are not configured")
        return False

    visitor_email = _visitor_email(form)
    visitor_name = _visitor_name(form)
    connection = email_settings.connection()

    context = {
        "company": email_settings.sender_name,
        "rows": _rows(form),
        "submitted_at": timezone.localtime(),
        "visitor_email": visitor_email,
        "visitor_name": visitor_name,
    }
    subject = page.subject or "Website enquiry"
    _send(
        f"{subject}: {visitor_name}" if visitor_name else subject,
        render_to_string("emails/enquiry_notification.txt", context),
        render_to_string("emails/enquiry_notification.html", context),
        email_settings,
        connection,
        to=[email_settings.contact_form_recipient],
        cc=[email_settings.contact_form_cc] if email_settings.contact_form_cc else None,
        reply_to=[visitor_email] if visitor_email else None,
    )

    if email_settings.send_confirmation_email and visitor_email:
        site = SiteSettings.load()
        # Anyone can submit someone else's address, so this deliberately does not repeat the
        # visitor's message or full name: the form must not be usable to send spam to third parties.
        thank_you_html = expand_db_html(page.thank_you_text)
        context = {
            "company": email_settings.sender_name,
            "first_name": _greeting_name(visitor_name),
            "thank_you_html": thank_you_html,
            "thank_you_text": unescape(strip_tags(thank_you_html.replace("</p>", "</p>\n\n"))).strip(),
            "phone": site.phone,
            "email": site.email,
        }
        try:
            _send(
                f"Thank you for contacting {email_settings.sender_name}",
                render_to_string("emails/enquiry_confirmation.txt", context),
                render_to_string("emails/enquiry_confirmation.html", context),
                email_settings,
                connection,
                to=[visitor_email],
            )
        except Exception:
            logger.exception("Enquiry notification sent, but the confirmation email failed")
    return True
