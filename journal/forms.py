from django import forms
from .models import JournalEntry, Tag
from django.contrib.auth.forms import PasswordChangeForm
from tinymce.widgets import TinyMCE
from django.utils.translation import gettext_lazy as _


class EntryForm(forms.ModelForm):
    # Remove colon ":" suffix from labels
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label_suffix = ""
        # Set initial tags if editing an existing entry
        if self.instance and self.instance.pk:
            self.fields['tags'].initial = ', '.join(tag.name for tag in self.instance.tags.all())
    
    # Title field with custom widget
    title = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Entry title (optional)')
        })
    )
    
    # Tags field as comma-separated string
    tags = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('comma, separated, tags'),
            'data-role': 'tagsinput'  # For potential JS tag input library
        }),
        help_text=_('Separate tags with commas')
    )
    
    # Content field with TinyMCE
    content = forms.CharField(
        widget=TinyMCE(
            attrs={
                'class': 'form-control',
                'rows': 15,
                'placeholder': _('Write your thoughts here...')
            },
            mce_attrs={
                'menubar': False,
                'plugins': 'link lists code help',
                'toolbar': 'undo redo | formatselect | bold italic backcolor | \
                           alignleft aligncenter alignright alignjustify | \
                           bullist numlist outdent indent | removeformat | help',
                'content_style': 'body { font-family: Arial, sans-serif; font-size: 16px; }',
                'branding': False,
                'elementpath': False,
                'statusbar': False,
            }
        )
    )
    
    # Date field
    date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
        })
    )

    class Meta:
        model = JournalEntry
        fields = ['title', 'date', 'content', 'tags']

    # this will automatically run when form.is_valid() called
    def clean_tags(self):
        tags = self.cleaned_data.get("tags")
        if tags:
            cleaned_tags = [tag.strip() for tag in tags.split(",")]
            return cleaned_tags
        else:
            return []

class ChangePasswordCustomForm(PasswordChangeForm):
    # remove colon ":" suffix from labels
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label_suffix = ""

    old_password = forms.CharField(widget=forms.PasswordInput(attrs={
        "class": "form-control",
        "placeholder": "Old password"
    }))

    new_password1 = forms.CharField(widget=forms.PasswordInput(attrs={
        "autocomplete": "new-password",
        "class": "form-control",
        "placeholder": "New password"
    }), label="New password")

    new_password2 = forms.CharField(widget=forms.PasswordInput(attrs={
        "autocomplete": "new-password",
        "class": "form-control",
        "placeholder": "Confirm new password"
    }), label="Confirm new password")

    class Meta:
        fields = ["old_password", "new_password1", "new_password2"]
