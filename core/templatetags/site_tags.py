from django import template
from wagtail.models import Page, Site

from core.models import ServicePage

register = template.Library()


@register.simple_tag(takes_context=True)
def site_root(context):
    request = context.get("request")
    return Site.find_for_request(request).root_page if request else None


@register.simple_tag(takes_context=True)
def main_menu(context):
    """Top-level live pages that have opted into the menu."""
    root = site_root(context)
    if not root:
        return Page.objects.none()
    return root.get_children().live().in_menu().specific()


@register.simple_tag
def children_of(page):
    if not page:
        return Page.objects.none()
    return page.get_children().live().in_menu().specific()


@register.simple_tag
def featured_standards(limit=8, featured_only=True):
    qs = ServicePage.objects.live().order_by("path")
    if featured_only:
        featured = qs.filter(featured=True)
        if featured.exists():
            qs = featured
    return qs[:limit]


@register.filter
def split_lines(value):
    if not value:
        return []
    return [line.strip() for line in str(value).splitlines() if line.strip()]


@register.filter
def rotating_split(heading):
    """Split a heading on the {word} placeholder so the middle can be animated."""
    text = str(heading or "")
    if "{word}" not in text:
        return [text, ""]
    before, _, after = text.partition("{word}")
    return [before, after]


@register.simple_tag
def link_url(link):
    """Resolve a LinkBlock value to a URL, preferring an explicit page choice."""
    if not link:
        return ""
    page = link.get("page")
    if page:
        return page.url
    return link.get("url") or ""
