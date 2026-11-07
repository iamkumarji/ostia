from wagtail.admin.panels import FieldPanel
from wagtail.fields import StreamField
from wagtail.models import Page

from core.blocks import SectionStreamBlock


class HomePage(Page):
    body = StreamField(SectionStreamBlock(), blank=True)

    content_panels = Page.content_panels + [FieldPanel("body")]
