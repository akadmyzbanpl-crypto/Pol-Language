from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator, URLValidator
from django.conf import settings
import uuid

class User(AbstractUser):
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=16,choices=[('student','دانشجو'),('teacher','استاد'),('admin','مدیر')],default='student')
    google_sub = models.CharField(max_length=255,unique=True,null=True,blank=True,editable=False)
    def __str__(self): return self.get_full_name() or self.username

class Course(models.Model):
    title=models.CharField('عنوان',max_length=150)
    category=models.CharField('گروه',max_length=20,choices=[('general','انگلیسی عمومی'),('ielts','آیلتس'),('conversation','مکالمه')])
    mode=models.CharField('نوع برگزاری',max_length=12,choices=[('online','آنلاین'),('onsite','حضوری')])
    level=models.CharField('سطح',max_length=12,default='A1')
    description=models.TextField('معرفی')
    syllabus=models.TextField('سرفصل‌ها',blank=True)
    price=models.PositiveIntegerField('شهریه (تومان)')
    capacity=models.PositiveIntegerField('ظرفیت',default=12,validators=[MinValueValidator(1)])
    total_sessions=models.PositiveIntegerField('تعداد جلسات',default=16,validators=[MinValueValidator(1)])
    schedule=models.CharField('برنامه زمانی',max_length=200,blank=True)
    start_date=models.DateField('تاریخ شروع',null=True,blank=True)
    teacher=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True,limit_choices_to={'role':'teacher'},related_name='teaching')
    published=models.BooleanField('منتشر شده',default=False)
    created=models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.title
    @property
    def seats(self): return max(0,self.capacity-self.enrollments.count())

class Enrollment(models.Model):
    student=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='enrollments')
    course=models.ForeignKey(Course,on_delete=models.PROTECT,related_name='enrollments')
    created=models.DateTimeField(auto_now_add=True)
    class Meta: constraints=[models.UniqueConstraint(fields=['student','course'],name='unique_enrollment')]
    def __str__(self): return f'{self.student} — {self.course}'

class Order(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    student=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    course=models.ForeignKey(Course,on_delete=models.PROTECT)
    amount=models.PositiveIntegerField('مبلغ تومان')
    status=models.CharField(max_length=24,choices=[('pending','در انتظار پرداخت'),('paid','پرداخت تأیید شد'),('review','پرداخت نیازمند بررسی ظرفیت')],default='pending')
    authority=models.CharField(max_length=128,null=True,blank=True,unique=True,editable=False)
    reference=models.CharField(max_length=128,blank=True,editable=False)
    created=models.DateTimeField(auto_now_add=True)
    class Meta: constraints=[models.UniqueConstraint(fields=['student','course'],name='unique_course_order')]

class Lesson(models.Model):
    course=models.ForeignKey(Course,on_delete=models.CASCADE,related_name='lessons')
    title=models.CharField('عنوان جلسه',max_length=150)
    starts=models.DateTimeField('زمان شروع')
    join_url=models.URLField('لینک کلاس',blank=True,validators=[URLValidator(schemes=['https'])])
    recording_url=models.URLField('لینک ضبط',blank=True,validators=[URLValidator(schemes=['https'])])
    resource_url=models.URLField('لینک منبع',blank=True,validators=[URLValidator(schemes=['https'])])
    completed=models.BooleanField('جلسه برگزار شد',default=False)
    def __str__(self): return f'{self.course} / {self.title}'

class Attendance(models.Model):
    lesson=models.ForeignKey(Lesson,on_delete=models.CASCADE)
    student=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    present=models.BooleanField(default=False)
    class Meta: constraints=[models.UniqueConstraint(fields=['lesson','student'],name='unique_attendance')]

class Grade(models.Model):
    course=models.ForeignKey(Course,on_delete=models.CASCADE)
    student=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    title=models.CharField(max_length=150)
    score=models.DecimalField(max_digits=5,decimal_places=2,validators=[MinValueValidator(0),MaxValueValidator(100)])
    feedback=models.TextField(blank=True)
    updated=models.DateTimeField(auto_now=True)

class PlacementResult(models.Model):
    student=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    score=models.PositiveIntegerField()
    level=models.CharField(max_length=12)
    answers=models.JSONField(default=list)
    created=models.DateTimeField(auto_now_add=True)

class Message(models.Model):
    sender=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='sent_messages')
    recipient=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,null=True,blank=True,related_name='received_messages')
    audience=models.CharField(max_length=16,choices=[('direct','مستقیم'),('all','همه'),('student','دانشجویان'),('teacher','استادان')],default='direct')
    subject=models.CharField(max_length=150)
    body=models.TextField()
    created=models.DateTimeField(auto_now_add=True)

class Ticket(models.Model):
    owner=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    subject=models.CharField(max_length=150)
    body=models.TextField()
    status=models.CharField(max_length=12,choices=[('open','باز'),('closed','بسته')],default='open')
    created=models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.subject

class TicketReply(models.Model):
    ticket=models.ForeignKey(Ticket,on_delete=models.CASCADE,related_name='replies')
    author=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    body=models.TextField()
    created=models.DateTimeField(auto_now_add=True)

class Audit(models.Model):
    actor=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True)
    action=models.CharField(max_length=100)
    detail=models.CharField(max_length=250,blank=True)
    created=models.DateTimeField(auto_now_add=True)

class LoginAttempt(models.Model):
    key=models.CharField(max_length=64,unique=True)
    count=models.PositiveIntegerField(default=0)
    started=models.DateTimeField(auto_now_add=True)

class LivePresence(models.Model):
    course=models.ForeignKey(Course,on_delete=models.CASCADE)
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    last_seen=models.DateTimeField(auto_now=True)
    hand=models.BooleanField(default=False)
    class Meta: constraints=[models.UniqueConstraint(fields=['course','user'],name='unique_presence')]

class ClassMessage(models.Model):
    course=models.ForeignKey(Course,on_delete=models.CASCADE)
    author=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    body=models.CharField(max_length=500)
    created=models.DateTimeField(auto_now_add=True)

class ClassroomControl(models.Model):
    course=models.OneToOneField(Course,on_delete=models.CASCADE)
    chat_open=models.BooleanField(default=True)

class StudyPlan(models.Model):
    result=models.OneToOneField(PlacementResult,on_delete=models.CASCADE)
    body=models.TextField(blank=True)
    requested=models.DateTimeField(auto_now_add=True)
