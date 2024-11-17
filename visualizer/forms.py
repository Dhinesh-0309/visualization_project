from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class SignupForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

class UploadFileForm(forms.Form):
    file = forms.FileField()
    
class QuestionForm(forms.Form):
    question = forms.CharField(max_length=500, widget=forms.Textarea(attrs={'placeholder': 'Ask a question about the data...'}))   
