from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

from .enquiries import is_spam
from .models import ContactPage

SUCCESS_MESSAGE = "Thank you. We have received your enquiry."


def _back_url(request, page):
    """The page the form was on, or the contact page if the Referer is missing or foreign."""
    referer = request.META.get("HTTP_REFERER", "")
    if url_has_allowed_host_and_scheme(
        referer, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return referer.split("#")[0] + "#enquiry-form"
    return f"{page.url}#enquiry-form"


@csrf_protect
@require_POST
def contact_form_submission(request):
    """Handles the Contact Form block, using the fields defined on the contact page."""
    page = ContactPage.objects.live().first()
    if page is None:
        raise Http404("There is no live contact page")

    back = _back_url(request, page)
    if is_spam(request):
        messages.success(request, SUCCESS_MESSAGE)
        return redirect(back)

    form = page.get_form(request.POST, request.FILES, page=page, user=request.user)
    if form.is_valid():
        page.process_form_submission(form)
        messages.success(request, SUCCESS_MESSAGE)
    else:
        for name, errors in form.errors.items():
            label = form.fields[name].label if name in form.fields else ""
            for error in errors:
                messages.error(request, f"{label}: {error}" if label else error)
    return redirect(back)
