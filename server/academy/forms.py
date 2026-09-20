from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Course, Lesson, Ticket, Grade

class SignupForm(UserCreationForm):
    first_name=forms.CharField(label='نام و نام خانوادگی',max_length=100)
    email=forms.EmailField(label='ایمیل')
    class Meta:
        model=User
        fields=['first_name','email','username','password1','password2']
    def clean_email(self):
        email=self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists(): raise forms.ValidationError('این ایمیل قبلاً ثبت شده است.')
        return email

class LoginForm(AuthenticationForm):
    username=forms.CharField(label='نام کاربری')
    password=forms.CharField(label='رمز عبور',widget=forms.PasswordInput)

class CourseForm(forms.ModelForm):
    class Meta:
        model=Course
        fields=['title','category','mode','level','description','syllabus','price','capacity','total_sessions','schedule','start_date','teacher','published']
        widgets={'start_date':forms.DateInput(attrs={'type':'date'}),'description':forms.Textarea(attrs={'rows':3}),'syllabus':forms.Textarea(attrs={'rows':3})}

class LessonForm(forms.ModelForm):
    class Meta:
        model=Lesson
        fields=['title','starts','join_url','recording_url','resource_url','completed']
        widgets={'starts':forms.DateTimeInput(attrs={'type':'datetime-local'},format='%Y-%m-%dT%H:%M')}

class TicketForm(forms.ModelForm):
    class Meta:
        model=Ticket
        fields=['subject','body']
        labels={'subject':'موضوع','body':'شرح درخواست'}
        widgets={'body':forms.Textarea(attrs={'rows':5})}

class GradeForm(forms.ModelForm):
    class Meta:
        model=Grade
        fields=['student','title','score','feedback']
        labels={'student':'دانشجو','title':'عنوان ارزیابی','score':'نمره از ۱۰۰','feedback':'بازخورد'}
        widgets={'feedback':forms.Textarea(attrs={'rows':3})}

class MessageForm(forms.Form):
    audience=forms.ChoiceField(label='مخاطب',choices=[('direct','پیام مستقیم'),('all','همه کاربران'),('student','دانشجویان'),('teacher','استادان')])
    recipient=forms.ModelChoiceField(label='گیرنده پیام مستقیم',queryset=User.objects.none(),required=False)
    subject=forms.CharField(label='موضوع',max_length=150)
    body=forms.CharField(label='متن پیام',max_length=10000,widget=forms.Textarea(attrs={'rows':4}))
    def __init__(self,*args,user,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['recipient'].queryset=User.objects.filter(is_active=True).exclude(pk=user.pk)
        if user.role != 'admin' and not user.is_superuser:
            self.fields['audience'].choices=[('direct','پیام مستقیم به همکار')]
            self.fields['recipient'].queryset=self.fields['recipient'].queryset.filter(role__in=['teacher','admin'])
    def clean(self):
        d=super().clean()
        if d.get('audience')=='direct' and not d.get('recipient'): self.add_error('recipient','گیرنده را انتخاب کنید.')
        return d
