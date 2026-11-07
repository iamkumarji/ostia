from django.db import models
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel, FieldRowPanel, InlinePanel, MultiFieldPanel
from wagtail.contrib.forms.models import AbstractEmailForm, AbstractFormField
from wagtail.contrib.forms.panels import FormSubmissionsPanel
from wagtail.contrib.settings.models import BaseGenericSetting, register_setting
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Page
from wagtail.search import index
from wagtail.snippets.models import register_snippet

from .blocks import SectionStreamBlock

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
                FieldRowPanel([FieldPanel("from_address"), FieldPanel("to_address")]),
                FieldPanel("subject"),
            ],
            heading="Email notification",
        ),
    ]
