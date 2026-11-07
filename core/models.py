import logging
from email.utils import formataddr

from django import forms
from django.core.mail import EmailMessage, get_connection
from django.db import models
from django.utils import timezone
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel, FieldRowPanel, HelpPanel, InlinePanel, MultiFieldPanel
from wagtail.contrib.forms.models import AbstractEmailForm, AbstractForm, AbstractFormField
from wagtail.contrib.forms.panels import FormSubmissionsPanel
from wagtail.contrib.settings.models import BaseGenericSetting, BaseSiteSetting, register_setting
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Page
from wagtail.search import index
from wagtail.snippets.models import register_snippet

from .blocks import SectionStreamBlock

logger = logging.getLogger(__name__)

STANDARD_CATEGORIES = [
    ("quality", "Quality"),
    ("environment", "Environment"),
    ("health-safety", "Health & Safety"),
    ("security", "Information Security"),
    ("food-medical", "Food & Medical"),
    ("energy-assets", "Energy & Assets"),
    ("governance", "Governance & Ethics"),
    ("product", "Product & Market Access"),
]

ACCENTS = [
    ("violet", "Violet"),
    ("coral", "Coral"),
    ("amber", "Amber"),
    ("mint", "Mint"),
    ("sky", "Sky"),
]


@register_setting(icon="cog")
class SiteSettings(BaseGenericSetting):
    phone = models.CharField(max_length=40, blank=True)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=255, blank=True)
    second_office = models.CharField(max_length=255, blank=True, help_text="Optional second office line")
    opening_hours = models.CharField(max_length=120, blank=True)
    client_login_url = models.URLField(blank=True)
    auditor_login_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    facebook_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)
    footer_blurb = models.TextField(blank=True)
    legal_line = models.CharField(max_length=255, blank=True)

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("phone"),
                FieldPanel("email"),
                FieldPanel("address"),
                FieldPanel("second_office"),
                FieldPanel("opening_hours"),
            ],
            heading="Contact details",
        ),
        MultiFieldPanel(
            [FieldPanel("client_login_url"), FieldPanel("auditor_login_url")],
            heading="Portals",
        ),
        MultiFieldPanel(
            [FieldPanel("linkedin_url"), FieldPanel("facebook_url"), FieldPanel("youtube_url")],
            heading="Social",
        ),
        FieldPanel("footer_blurb"),
        FieldPanel("legal_line"),
    ]

    class Meta:
        verbose_name = "Site settings"


@register_setting(icon="mail")
class EmailSettings(BaseSiteSetting):
    """SMTP details for enquiry emails, kept here so they can change without a deploy."""

    email_backend = models.CharField(
        max_length=255, default="django.core.mail.backends.smtp.EmailBackend", editable=False
    )
    smtp_host = models.CharField(
        "SMTP host", max_length=255, blank=True, help_text="For example smtp.gmail.com"
    )
    smtp_port = models.IntegerField("SMTP port", default=587, help_text="587 for TLS, 465 for SSL")
    use_tls = models.BooleanField("Use TLS", default=True, help_text="Recommended for port 587")
    use_ssl = models.BooleanField(
        "Use SSL", default=False, help_text="For port 465. Ignored if TLS is also ticked"
    )
    smtp_username = models.CharField("SMTP username", max_length=255, blank=True)
    smtp_password = models.CharField(
        "SMTP password",
        max_length=255,
        blank=True,
        help_text=(
            "Most providers need an app password. Leave blank to keep the current one. "
            "It is stored unencrypted, so only give trusted users access to this page."
        ),
    )
    sender_name = models.CharField(
        max_length=80, default="Ostia Management", help_text="Shown as the sender and in the emails"
    )
    from_email = models.EmailField(
        "From email", blank=True, help_text="Most providers require this to match the SMTP mailbox"
    )
    contact_form_recipient = models.EmailField(
        blank=True, help_text="Where enquiries are sent"
    )
    contact_form_cc = models.EmailField("Contact form CC", blank=True)
    send_confirmation_email = models.BooleanField(
        "Send confirmation to visitor",
        default=True,
        help_text="Uses the thank-you text from the contact page",
    )
    test_email = models.EmailField(
        "Send a test email to",
        blank=True,
        help_text="Enter an address and save. The result appears below and this field clears.",
    )
    is_configured = models.BooleanField("Ready to send", default=False, editable=False)
    last_test_date = models.DateTimeField("Last tested", null=True, blank=True, editable=False)
    last_test_status = models.CharField("Last test result", max_length=255, blank=True, editable=False)

    panels = [
        HelpPanel(
            "Host, username, password, from email and recipient are all needed before email is sent. "
            "Until then, enquiries are still saved under Forms."
        ),
        MultiFieldPanel(
            [
                FieldRowPanel([FieldPanel("smtp_host"), FieldPanel("smtp_port")]),
                FieldRowPanel([FieldPanel("use_tls"), FieldPanel("use_ssl")]),
                FieldPanel("smtp_username"),
                FieldPanel(
                    "smtp_password",
                    widget=forms.PasswordInput(
                        render_value=False, attrs={"autocomplete": "new-password"}
                    ),
                ),
            ],
            heading="SMTP server",
        ),
        MultiFieldPanel(
            [
                FieldPanel("sender_name"),
                FieldPanel("from_email"),
                FieldPanel("contact_form_recipient"),
                FieldPanel("contact_form_cc"),
                FieldPanel("send_confirmation_email"),
            ],
            heading="Addresses and options",
        ),
        MultiFieldPanel(
            [
                FieldPanel("test_email"),
                FieldPanel("is_configured", read_only=True),
                FieldPanel("last_test_date", read_only=True),
                FieldPanel("last_test_status", read_only=True),
            ],
            heading="Test",
        ),
    ]

    class Meta:
        verbose_name = "Email settings"

    def __str__(self):
        return "Email settings"

    @property
    def sender(self):
        return formataddr((self.sender_name, self.from_email))

    def connection(self):
        """An explicit connection, so these details never touch Django's global settings."""
        return get_connection(
            backend=self.email_backend,
            host=self.smtp_host,
            port=self.smtp_port,
            username=self.smtp_username,
            password=self.smtp_password,
            use_tls=self.use_tls,
            use_ssl=self.use_ssl,
            timeout=15,
            fail_silently=False,
        )

    def _send_test_email(self):
        self.last_test_date = timezone.now()
        if not self.is_configured:
            self.last_test_status = "Not sent: fill in the required fields first."
            return
        try:
            EmailMessage(
                subject="Email settings test",
                body=f"This test confirms that {self.sender_name} can send email through {self.smtp_host}.",
                from_email=self.sender,
                to=[self.test_email],
                connection=self.connection(),
            ).send(fail_silently=False)
            self.last_test_status = f"Sent to {self.test_email}. Check that it arrived."
        except Exception as error:
            logger.exception("Test email failed")
            self.last_test_status = f"Failed: {type(error).__name__}: {error}"[:255]

    def save(self, *args, **kwargs):
        # The password box never shows the stored value, so blank means "keep it".
        if not self.smtp_password and self.pk:
            self.smtp_password = (
                type(self).objects.filter(pk=self.pk).values_list("smtp_password", flat=True).first() or ""
            )
        # Django refuses to send with both set.
        if self.use_tls and self.use_ssl:
            self.use_ssl = False
        self.is_configured = bool(
            self.smtp_host
            and self.smtp_username
            and self.smtp_password
            and self.from_email
            and self.contact_form_recipient
        )
        if self.test_email:
            self._send_test_email()
            self.test_email = ""
        super().save(*args, **kwargs)


def image_field(help_text=""):
    return models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text=help_text,
    )


class HeaderMixin(models.Model):
    """Shared page-header fields. The eyebrow sits above the H1 in the hero band."""

    eyebrow = models.CharField(max_length=80, blank=True)
    intro = models.TextField(blank=True, help_text="Shown in the page header")
    header_image = image_field("Background photo for the page header")

    header_panels = [FieldPanel("eyebrow"), FieldPanel("intro"), FieldPanel("header_image")]

    class Meta:
        abstract = True


class StandardPage(HeaderMixin, Page):
    """A flexible page built entirely from content sections."""

    body = StreamField(SectionStreamBlock(), blank=True)

    content_panels = Page.content_panels + HeaderMixin.header_panels + [FieldPanel("body")]
    search_fields = Page.search_fields + [index.SearchField("intro")]


class ServiceIndexPage(HeaderMixin, Page):
    body = StreamField(SectionStreamBlock(), blank=True)

    subpage_types = ["core.ServicePage"]
    content_panels = Page.content_panels + HeaderMixin.header_panels + [FieldPanel("body")]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        services = ServicePage.objects.child_of(self).live().order_by("path")
        labels = dict(STANDARD_CATEGORIES)
        groups = []
        for key, _ in STANDARD_CATEGORIES:
            matching = [s for s in services if s.category == key]
            if matching:
                groups.append((key, labels[key], matching))
        context["groups"] = groups
        context["services"] = services
        return context


class ServicePage(HeaderMixin, Page):
    code = models.CharField(max_length=60, help_text="e.g. ISO 9001:2015")
    category = models.CharField(max_length=30, choices=STANDARD_CATEGORIES, default="quality")
    system_name = models.CharField(
        max_length=120, blank=True, help_text="e.g. Quality Management System"
    )
    accent = models.CharField(max_length=20, choices=ACCENTS, default="violet")
    summary = models.TextField(help_text="One or two sentences used on cards and in the page header")
    accredited = models.BooleanField(
        default=False, help_text="Tick when the scheme sits inside the UAF accredited scope"
    )
    featured = models.BooleanField(default=False, help_text="Show on the home page and in the footer")
    image = image_field("Used in the page header, cards and the home page showcase")
    overview = RichTextField(blank=True)
    benefits = models.TextField(blank=True, help_text="One benefit per line")
    body = StreamField(SectionStreamBlock(), blank=True)

    parent_page_types = ["core.ServiceIndexPage"]
    content_panels = Page.content_panels + [
        FieldRowPanel([FieldPanel("code"), FieldPanel("category")]),
        FieldRowPanel([FieldPanel("system_name"), FieldPanel("accent")]),
        FieldPanel("summary"),
        FieldRowPanel([FieldPanel("accredited"), FieldPanel("featured")]),
        FieldPanel("image"),
        FieldPanel("overview"),
        FieldPanel("benefits"),
        FieldPanel("body"),
    ]
    search_fields = Page.search_fields + [
        index.SearchField("summary"),
        index.SearchField("overview"),
        index.AutocompleteField("code"),
    ]

    @property
    def benefit_list(self):
        return [line.strip() for line in self.benefits.splitlines() if line.strip()]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["related"] = (
            ServicePage.objects.live().sibling_of(self, inclusive=False).filter(category=self.category)[:3]
        )
        return context


@register_snippet
class Certificate(models.Model):
    """Backs the public certificate check on the Verify page."""

    STATUS = [
        ("active", "Active"),
        ("suspended", "Suspended"),
        ("withdrawn", "Withdrawn"),
        ("expired", "Expired"),
    ]

    number = models.CharField(max_length=40, unique=True, help_text="e.g. OML-00012-Q")
    holder = models.CharField(max_length=160)
    standard = models.CharField(max_length=80, help_text="e.g. ISO 9001:2015")
    scope = models.TextField(blank=True)
    site_address = models.CharField(max_length=255, blank=True)
    issued = models.DateField()
    expires = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS, default="active")

    panels = [
        FieldRowPanel([FieldPanel("number"), FieldPanel("status")]),
        FieldPanel("holder"),
        FieldPanel("standard"),
        FieldPanel("scope"),
        FieldPanel("site_address"),
        FieldRowPanel([FieldPanel("issued"), FieldPanel("expires")]),
    ]

    class Meta:
        ordering = ["number"]

    def __str__(self):
        return f"{self.number} - {self.holder}"


class VerifyPage(HeaderMixin, Page):
    """Looks a certificate up by number. Read-only, so a GET query is fine."""

    body = StreamField(SectionStreamBlock(), blank=True)
    help_text_above_form = models.CharField(max_length=255, blank=True)

    content_panels = Page.content_panels + HeaderMixin.header_panels + [
        FieldPanel("help_text_above_form"),
        FieldPanel("body"),
    ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        number = (request.GET.get("number") or "").strip()
        context["query"] = number
        if number:
            context["searched"] = True
            context["certificate"] = Certificate.objects.filter(number__iexact=number).first()
        return context


class ContactFormField(AbstractFormField):
    page = ParentalKey("ContactPage", on_delete=models.CASCADE, related_name="form_fields")


class ContactPage(HeaderMixin, AbstractEmailForm):
    body = StreamField(SectionStreamBlock(), blank=True)
    thank_you_text = RichTextField(blank=True)

    content_panels = AbstractEmailForm.content_panels + HeaderMixin.header_panels + [
        FormSubmissionsPanel(),
        InlinePanel("form_fields", label="Form fields"),
        FieldPanel("thank_you_text"),
        FieldPanel("body"),
        MultiFieldPanel(
            [
                HelpPanel("Addresses and the mail server are set in Settings > Email settings."),
                FieldPanel("subject"),
            ],
            heading="Email notification",
        ),
    ]

    def serve(self, request, *args, **kwargs):
        from .enquiries import is_spam

        if request.method == "POST" and is_spam(request):
            return self.render_landing_page(request)
        return super().serve(request, *args, **kwargs)

    def process_form_submission(self, form):
        """Save the enquiry first, so that a mail failure cannot lose it."""
        from .enquiries import send_enquiry_emails

        submission = AbstractForm.process_form_submission(self, form)
        try:
            send_enquiry_emails(self, form)
        except Exception:
            logger.exception("Enquiry %s was saved but could not be emailed", submission.pk)
        return submission
