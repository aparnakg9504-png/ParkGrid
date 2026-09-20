
from django import forms
from django.contrib.auth import get_user_model
from .models import Complaint

User = get_user_model()


class RegistrationForm(forms.ModelForm):

    full_name = forms.CharField(
        max_length=150,
        required=True
    )

    password = forms.CharField(
        widget=forms.PasswordInput,
        min_length=8
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput,
        min_length=8
    )

    class Meta:
        model = User
        fields = [
            'full_name',
            'email',
            'phone',
            'password',
            'confirm_password',
        ]

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()

        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                'An account with this email already exists.'
            )

        return email

    def clean(self):
        cleaned_data = super().clean()

        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password:
            if password != confirm_password:
                raise forms.ValidationError(
                    'Passwords do not match.'
                )

        return cleaned_data
class ComplaintForm(forms.ModelForm):

    class Meta:
        model = Complaint
        fields = [
            'location',
            'subject',
            'description',
            'photo',
        ]