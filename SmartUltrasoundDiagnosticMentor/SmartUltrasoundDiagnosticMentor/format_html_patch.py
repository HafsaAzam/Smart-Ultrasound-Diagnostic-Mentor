"""
Django 6.0 compatibility patch for format_html.

Django 6.0 changed format_html() to require at least one arg/kwarg.
Jazzmin (and possibly other packages) call format_html(some_string)
with no args, which now raises TypeError.

This monkey-patch restores the old behavior: if no args/kwargs are
provided, it falls back to mark_safe (the pre-6.0 behavior).
"""
from django.utils import html as _html_module
from django.utils.safestring import mark_safe

_original_format_html = _html_module.format_html


def _compat_format_html(format_string, *args, **kwargs):
    if not args and not kwargs:
        return mark_safe(format_string)
    return _original_format_html(format_string, *args, **kwargs)


_html_module.format_html = _compat_format_html
