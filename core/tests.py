from django.contrib.messages import get_messages
from django.core import mail
from django.core.mail.backends.base import BaseEmailBackend
from django.test import Client, TestCase
from wagtail.models import Site

from .models import ContactFormField, ContactPage, EmailSettings, StandardPage

LOCMEM = "django.core.mail.backends.locmem.EmailBackend"
SUBMIT = "/contact/submit/"


class FailingBackend(BaseEmailBackend):
    def send_messages(self, messages):
        raise OSError("SMTP is down")


class ConfirmationFailsBackend(BaseEmailBackend):
    """Delivers the team's notification, then fails on the visitor's confirmation."""

    def send_messages(self, messages):
        if messages[0].to == ["visitor@example.com"]:
            raise OSError("Mailbox unavailable")
        mail.outbox.extend(messages)
        return len(messages)


class EnquiryTestCase(TestCase):
    def setUp(self):
        self.site = Site.objects.get(is_default_site=True)
        self.page = ContactPage(
            title="Contact",
            slug="contact-test",
            subject="Website enquiry",
            thank_you_text="<p>We reply within one working day.</p>",
        )
        self.site.root_page.add_child(instance=self.page)
        fields = [
            ("Your name", "singleline", True),
            ("Email address", "email", True),
            ("Your message", "multiline", True),
            ("Telephone", "singleline", False),
        ]
        for order, (label, field_type, required) in enumerate(fields):
            ContactFormField.objects.create(
                page=self.page, sort_order=order, label=label, field_type=field_type, required=required
            )
        self.data = {
            "your_name": "Ada <b>Lovelace</b>",
            "email_address": "visitor@example.com",
            "your_message": "<script>alert(1)</script>",
        }
        self.settings = EmailSettings.for_site(self.site)

    def configure(self, **overrides):
        values = {
            "email_backend": LOCMEM,
            "smtp_host": "mail.example.com",
            "smtp_username": "user",
            "smtp_password": "secret",
            "from_email": "web@example.com",
            "contact_form_recipient": "team@example.com",
            "contact_form_cc": "cc@example.com",
        }
        values.update(overrides)
        for name, value in values.items():
            setattr(self.settings, name, value)
        self.settings.save()

    def submissions(self):
        return self.page.get_submission_class().objects.filter(page=self.page).count()


class SubmitViewTests(EnquiryTestCase):
    def test_saves_and_sends_both_emails(self):
        self.configure()
        response = self.client.post(SUBMIT, self.data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.submissions(), 1)
        self.assertEqual(len(mail.outbox), 2)

        notification, confirmation = mail.outbox
        self.assertEqual(notification.to, ["team@example.com"])
        self.assertEqual(notification.cc, ["cc@example.com"])
        self.assertEqual(notification.reply_to, ["visitor@example.com"])
        self.assertEqual(notification.from_email, "Ostia Management <web@example.com>")
        self.assertEqual(confirmation.to, ["visitor@example.com"])

    def test_html_email_escapes_visitor_input(self):
        self.configure()
        self.client.post(SUBMIT, self.data)
        html = mail.outbox[0].alternatives[0][0]
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertIn("<script>", mail.outbox[0].body)

    def test_every_field_reaches_the_inbox(self):
        self.configure()
        self.client.post(SUBMIT, {**self.data, "telephone": "01234 567890"})
        self.assertIn("01234 567890", mail.outbox[0].body)

    def test_confirmation_cannot_carry_third_party_spam(self):
        self.configure()
        self.client.post(SUBMIT, {**self.data, "your_name": "Buy http://spam.example now"})
        confirmation = mail.outbox[1]
        self.assertNotIn("<script>", confirmation.body)
        self.assertNotIn("spam.example", confirmation.body)
        self.assertIn("one working day", confirmation.body)

    def test_plain_text_confirmation_keeps_paragraphs_apart(self):
        self.page.thank_you_text = "<p>First.</p><p>Second &amp; last.</p>"
        self.page.save()
        self.configure()
        self.client.post(SUBMIT, self.data)
        self.assertIn("First.\n\nSecond & last.", mail.outbox[1].body)

    def test_link_as_name_is_left_out_of_the_greeting(self):
        self.configure()
        self.client.post(SUBMIT, {**self.data, "your_name": "http://spam.example"})
        self.assertNotIn("spam.example", mail.outbox[1].body)
        self.assertNotIn("spam.example", mail.outbox[1].alternatives[0][0])

    def test_confirmation_can_be_turned_off(self):
        self.configure(send_confirmation_email=False)
        self.client.post(SUBMIT, self.data)
        self.assertEqual(len(mail.outbox), 1)

    def test_newline_in_name_cannot_inject_headers(self):
        self.configure()
        self.client.post(SUBMIT, {**self.data, "your_name": "Ada\r\nBcc: victim@example.com"})
        self.assertEqual(mail.outbox[0].subject, "Website enquiry: Ada Bcc: victim@example.com")

    def test_unconfigured_still_saves(self):
        response = self.client.post(SUBMIT, self.data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.submissions(), 1)
        self.assertEqual(mail.outbox, [])

    def test_smtp_failure_keeps_the_enquiry(self):
        self.configure(email_backend="core.tests.FailingBackend")
        with self.assertLogs("core.models", level="ERROR"):
            response = self.client.post(SUBMIT, self.data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.submissions(), 1)

    def test_failed_confirmation_does_not_affect_the_notification(self):
        self.configure(email_backend="core.tests.ConfirmationFailsBackend")
        with self.assertLogs("core.enquiries", level="ERROR"):
            response = self.client.post(SUBMIT, self.data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual([m.to for m in mail.outbox], [["team@example.com"]])

    def test_honeypot_drops_silently(self):
        self.configure()
        response = self.client.post(SUBMIT, {**self.data, "contact_website": "http://spam.example"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.submissions(), 0)
        self.assertEqual(mail.outbox, [])
        self.assertEqual(get_messages(response.wsgi_request)._queued_messages[0].level_tag, "success")

    def test_invalid_input_is_rejected_with_a_message(self):
        self.configure()
        response = self.client.post(SUBMIT, {**self.data, "email_address": "nope"})
        self.assertEqual(self.submissions(), 0)
        self.assertEqual(mail.outbox, [])
        queued = get_messages(response.wsgi_request)._queued_messages
        self.assertEqual(queued[0].level_tag, "error")
        self.assertIn("Email address", queued[0].message)

    def test_get_not_allowed(self):
        self.assertEqual(self.client.get(SUBMIT).status_code, 405)

    def test_csrf_enforced(self):
        response = Client(enforce_csrf_checks=True).post(SUBMIT, self.data)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.submissions(), 0)

    def test_redirect_returns_to_same_site_referer(self):
        response = self.client.post(SUBMIT, self.data, HTTP_REFERER="http://testserver/about/#x")
        self.assertEqual(response["Location"], "http://testserver/about/#enquiry-form")

    def test_redirect_ignores_foreign_referer(self):
        response = self.client.post(SUBMIT, self.data, HTTP_REFERER="https://evil.example/")
        self.assertEqual(response["Location"], f"{self.page.url}#enquiry-form")


class ContactPageTests(EnquiryTestCase):
    def test_own_form_saves_and_sends(self):
        self.configure()
        response = self.client.post(self.page.url, self.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.submissions(), 1)
        self.assertEqual(len(mail.outbox), 2)

    def test_own_form_honeypot(self):
        self.configure()
        response = self.client.post(self.page.url, {**self.data, "contact_website": "x"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.submissions(), 0)
        self.assertEqual(mail.outbox, [])

    def test_own_form_shows_errors_inline(self):
        response = self.client.post(self.page.url, {**self.data, "email_address": "nope"})
        self.assertContains(response, "errorlist")
        self.assertEqual(self.submissions(), 0)


class ContactFormBlockTests(EnquiryTestCase):
    def test_block_renders_form_with_csrf_and_shows_result(self):
        self.configure()
        page = StandardPage(
            title="Block page",
            slug="block-page",
            body=[("contact_form", {"heading": "Ask us", "tone": "tint"})],
        )
        self.site.root_page.add_child(instance=page)

        response = self.client.get(page.url)
        self.assertContains(response, f'action="{SUBMIT}"')
        self.assertContains(response, "csrfmiddlewaretoken")
        self.assertContains(response, 'name="email_address"')

        response = self.client.post(SUBMIT, self.data, HTTP_REFERER=f"http://testserver{page.url}", follow=True)
        self.assertContains(response, "We have received your enquiry")
        self.assertEqual(self.submissions(), 1)


class EmailSettingsTests(EnquiryTestCase):
    def test_is_configured_needs_all_required_fields(self):
        self.configure(contact_form_recipient="")
        self.assertFalse(self.settings.is_configured)
        self.configure()
        self.assertTrue(self.settings.is_configured)

    def test_tls_wins_over_ssl(self):
        self.configure(use_tls=True, use_ssl=True)
        self.assertFalse(self.settings.use_ssl)

    def test_blank_password_keeps_the_stored_one(self):
        self.configure()
        self.settings.smtp_password = ""
        self.settings.save()
        self.settings.refresh_from_db()
        self.assertEqual(self.settings.smtp_password, "secret")

    def test_test_email_is_one_shot(self):
        self.configure(test_email="me@example.com")
        self.assertEqual(mail.outbox[0].to, ["me@example.com"])
        self.assertEqual(self.settings.test_email, "")
        self.assertIn("Sent to me@example.com", self.settings.last_test_status)
        self.settings.save()
        self.assertEqual(len(mail.outbox), 1)

    def test_test_email_failure_is_reported_without_blocking_save(self):
        with self.assertLogs("core.models", level="ERROR"):
            self.configure(email_backend="core.tests.FailingBackend", test_email="me@example.com")
        self.settings.refresh_from_db()
        self.assertIn("Failed: OSError", self.settings.last_test_status)

    def test_test_email_needs_configuration(self):
        self.settings.test_email = "me@example.com"
        self.settings.save()
        self.assertIn("Not sent", self.settings.last_test_status)
        self.assertEqual(mail.outbox, [])
