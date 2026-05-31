# Apply Django 6.0 format_html compatibility patch
# This must run before any admin/template code imports format_html
import SmartUltrasoundDiagnosticMentor.format_html_patch  # noqa: F401
