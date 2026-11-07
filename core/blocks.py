"""Content sections for Ostia Management.

Every block renders from templates/blocks/<name>.html. Blocks carry presentation
choices (tone, style) so editors can vary the rhythm of a page without new code.
"""
from wagtail import blocks
from wagtail.documents.blocks import DocumentChooserBlock
from wagtail.images.blocks import ImageChooserBlock

TONES = [
    ("paper", "Paper (white)"),
    ("tint", "Tint (light grey)"),
    ("ink", "Ink (near black)"),
    ("grad", "Gradient (lavender to peach)"),
]


class LinkBlock(blocks.StructBlock):
    label = blocks.CharBlock(required=False)
    url = blocks.CharBlock(required=False, help_text="Relative (/contact/) or absolute URL")
    page = blocks.PageChooserBlock(required=False, help_text="Overrides the URL above")

    class Meta:
        icon = "link"


class SectionHeadingMixin(blocks.StructBlock):
    eyebrow = blocks.CharBlock(required=False)
    heading = blocks.CharBlock(required=False)
    intro = blocks.TextBlock(required=False)


class HeroBlock(blocks.StructBlock):
    eyebrow = blocks.CharBlock(required=False)
    heading = blocks.CharBlock()
    rotating_words = blocks.ListBlock(
        blocks.CharBlock(), required=False, default=[], help_text="Cycled in place of {word} in the heading"
    )
    intro = blocks.TextBlock(required=False)
    primary_cta = LinkBlock(required=False)
    secondary_cta = LinkBlock(required=False)
    highlights = blocks.ListBlock(blocks.CharBlock(), required=False, default=[])
    image = ImageChooserBlock(required=False)

    class Meta:
        icon = "home"
        template = "blocks/hero.html"


class MarqueeBlock(blocks.StructBlock):
    items = blocks.ListBlock(blocks.CharBlock())
    speed = blocks.ChoiceBlock(choices=[("slow", "Slow"), ("medium", "Medium"), ("fast", "Fast")], default="medium")

    class Meta:
        icon = "arrows-up-down"
        template = "blocks/marquee.html"


class StatItem(blocks.StructBlock):
    value = blocks.CharBlock(help_text="Digits count up; any prefix or suffix such as + or % is kept")
    label = blocks.CharBlock()


class StatsBlock(SectionHeadingMixin):
    items = blocks.ListBlock(StatItem())
    tone = blocks.ChoiceBlock(choices=TONES, default="tint")

    class Meta:
        icon = "order"
        template = "blocks/stats.html"


class FeatureSplitBlock(SectionHeadingMixin):
    body = blocks.RichTextBlock(required=False)
    points = blocks.ListBlock(blocks.CharBlock(), required=False, default=[])
    cta = LinkBlock(required=False)
    image = ImageChooserBlock(required=False)
    reverse = blocks.BooleanBlock(required=False, help_text="Put the visual on the left")
    tone = blocks.ChoiceBlock(choices=TONES, default="paper")

    class Meta:
        icon = "doc-full"
        template = "blocks/feature_split.html"


class Card(blocks.StructBlock):
    badge = blocks.CharBlock(required=False, help_text="Short label, e.g. ISO 9001")
    title = blocks.CharBlock()
    text = blocks.TextBlock(required=False)
    icon = blocks.CharBlock(required=False, help_text="Single emoji or glyph used as the card marker")
    image = ImageChooserBlock(required=False)
    page = blocks.PageChooserBlock(required=False)
    url = blocks.CharBlock(required=False)


class CardGridBlock(SectionHeadingMixin):
    cards = blocks.ListBlock(Card())
    style = blocks.ChoiceBlock(
        choices=[
            ("panel", "Dark slab (middle card highlighted)"),
            ("plain", "Plain cards"),
            ("numbered", "Numbered"),
            ("tabs", "Tabbed panel (badge = tab label)"),
        ],
        default="plain",
    )
    tone = blocks.ChoiceBlock(choices=TONES, default="paper")

    class Meta:
        icon = "table"
        template = "blocks/card_grid.html"


class ProcessStep(blocks.StructBlock):
    title = blocks.CharBlock()
    text = blocks.TextBlock(required=False)
    meta = blocks.CharBlock(required=False, help_text="Small label, e.g. Stage 1")


class ProcessBlock(SectionHeadingMixin):
    steps = blocks.ListBlock(ProcessStep())
    style = blocks.ChoiceBlock(
        choices=[
            ("steps", "Numbered rows"),
            ("track", "Horizontal track"),
            ("cycle", "Certification cycle diagram (needs exactly 6 steps)"),
        ],
        default="steps",
    )
    tone = blocks.ChoiceBlock(choices=TONES, default="tint")

    class Meta:
        icon = "list-ol"
        template = "blocks/process.html"


class ChipCloudBlock(SectionHeadingMixin):
    chips = blocks.ListBlock(blocks.CharBlock())
    tone = blocks.ChoiceBlock(choices=TONES, default="paper")

    class Meta:
        icon = "tag"
        template = "blocks/chip_cloud.html"


class Testimonial(blocks.StructBlock):
    quote = blocks.TextBlock()
    name = blocks.CharBlock()
    organisation = blocks.CharBlock(required=False)
    rating = blocks.IntegerBlock(min_value=1, max_value=5, default=5)


class TestimonialsBlock(SectionHeadingMixin):
    items = blocks.ListBlock(Testimonial())
    tone = blocks.ChoiceBlock(choices=TONES, default="ink")

    class Meta:
        icon = "openquote"
        template = "blocks/testimonials.html"


class CertificateSpecimen(blocks.StructBlock):
    number = blocks.CharBlock(help_text="e.g. OML-00012-Q")
    standard = blocks.CharBlock(help_text="e.g. ISO 9001:2015")
    holder = blocks.CharBlock(default="Specimen Holding Ltd.")
    issued = blocks.CharBlock(help_text="e.g. 14 Mar 2024")
    expires = blocks.CharBlock(help_text="e.g. 13 Mar 2027")
    scope = blocks.TextBlock(required=False)


class CertificateShowcaseBlock(SectionHeadingMixin):
    items = blocks.ListBlock(CertificateSpecimen())
    tone = blocks.ChoiceBlock(choices=TONES, default="tint")

    class Meta:
        icon = "doc-empty"
        template = "blocks/certificates.html"


class TeamMember(blocks.StructBlock):
    name = blocks.CharBlock()
    role = blocks.CharBlock(required=False)
    experience = blocks.CharBlock(required=False, help_text="e.g. 30+ years")
    bio = blocks.TextBlock(required=False)
    image = ImageChooserBlock(required=False)


class TeamBlock(SectionHeadingMixin):
    members = blocks.ListBlock(TeamMember())

    class Meta:
        icon = "group"
        template = "blocks/team.html"


class FAQItem(blocks.StructBlock):
    question = blocks.CharBlock()
    answer = blocks.TextBlock()


class FAQBlock(SectionHeadingMixin):
    items = blocks.ListBlock(FAQItem())
    tone = blocks.ChoiceBlock(choices=TONES, default="paper")

    class Meta:
        icon = "help"
        template = "blocks/faq.html"


class DocumentCardBlock(SectionHeadingMixin):
    title = blocks.CharBlock(help_text="e.g. Annex E - Certification Process")
    description = blocks.TextBlock(required=False)
    pages = blocks.CharBlock(required=False, help_text="e.g. 14 pages")
    document = DocumentChooserBlock(required=False)
    url = blocks.CharBlock(required=False, help_text="Used when no document is uploaded")

    class Meta:
        icon = "doc-full-inverse"
        template = "blocks/document_card.html"


class CTABlock(blocks.StructBlock):
    heading = blocks.CharBlock()
    text = blocks.TextBlock(required=False)
    button = LinkBlock(required=False)
    secondary = LinkBlock(required=False)

    class Meta:
        icon = "pick"
        template = "blocks/cta.html"


class RichTextSectionBlock(SectionHeadingMixin):
    body = blocks.RichTextBlock()
    tone = blocks.ChoiceBlock(choices=TONES, default="paper")

    class Meta:
        icon = "pilcrow"
        template = "blocks/rich_text.html"


class StandardsShowcaseBlock(SectionHeadingMixin):
    """Pulls live ServicePage records so the grid never drifts from the page tree."""

    limit = blocks.IntegerBlock(default=8, min_value=3, max_value=24)
    featured_only = blocks.BooleanBlock(required=False, default=True)
    tone = blocks.ChoiceBlock(choices=TONES, default="tint")

    class Meta:
        icon = "list-ul"
        template = "blocks/standards_showcase.html"


class SectionStreamBlock(blocks.StreamBlock):
    hero = HeroBlock()
    marquee = MarqueeBlock()
    stats = StatsBlock()
    feature = FeatureSplitBlock()
    cards = CardGridBlock()
    standards = StandardsShowcaseBlock()
    process = ProcessBlock()
    chips = ChipCloudBlock()
    certificates = CertificateShowcaseBlock()
    testimonials = TestimonialsBlock()
    team = TeamBlock()
    faq = FAQBlock()
    document = DocumentCardBlock()
    cta = CTABlock()
    text = RichTextSectionBlock()
