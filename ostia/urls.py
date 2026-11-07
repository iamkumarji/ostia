from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve
from wagtail import urls as wagtail_urls
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.documents import urls as wagtaildocs_urls

from core.views import contact_form_submission

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("admin/", include(wagtailadmin_urls)),
    path("documents/", include(wagtaildocs_urls)),
    path("contact/submit/", contact_form_submission, name="contact_form_submit"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.BASE_DIR / "static")
else:
    # Static files are collected ahead of time and handed to WhiteNoise, but
    # Wagtail writes image renditions under MEDIA_ROOT the first time a page
    # renders them. That prefix therefore has to be served from the filesystem
    # on each request, not from a listing taken once at startup.
    urlpatterns += [
        re_path(
            r"^%s(?P<path>.*)$" % settings.MEDIA_URL.lstrip("/"),
            serve,
            {"document_root": settings.MEDIA_ROOT},
        )
    ]

urlpatterns += [path("", include(wagtail_urls))]
