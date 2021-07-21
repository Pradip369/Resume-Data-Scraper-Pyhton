from django import forms


class PdfUploadForm(forms.Form):
    enter_url  = forms.URLField(required = True)