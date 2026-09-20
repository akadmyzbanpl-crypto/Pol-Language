import secrets
from datetime import timedelta
from django.core.management.base import BaseCommand,CommandError
from django.conf import settings
from django.utils import timezone
from academy.models import *

class Command(BaseCommand):
    help='Create optional local demo data; never run against production.'
    def handle(self,*args,**options):
        if not settings.DEBUG or not settings.POL_DEMO: raise CommandError('Demo data requires POL_DEBUG=1 and POL_DEMO=1.')
        people={}
        for role,name in [('student','دانشجوی نمونه'),('teacher','استاد نمونه'),('admin','مدیر نمونه')]:
            u,new=User.objects.get_or_create(username='demo_'+role,defaults={'email':role+'@example.invalid','first_name':name,'role':role})
            if new:
                password=secrets.token_urlsafe(14);u.set_password(password);u.save()
                self.stdout.write(f'{u.username}: {password}')
            people[role]=u
        entries=[('انگلیسی عمومی | شروع مطمئن','general','onsite','A1',2400000,'شنبه و دوشنبه · ۱۷:۰۰'),('آمادگی آیلتس | یک هدف روشن','ielts','online','B2',3800000,'یکشنبه و سه‌شنبه · ۱۹:۰۰'),('مکالمه انگلیسی | روان‌تر صحبت کن','conversation','online','B1',2900000,'دوشنبه و چهارشنبه · ۱۸:۰۰')]
        for i,(title,category,mode,level,price,schedule) in enumerate(entries):
            c,_=Course.objects.get_or_create(title=title,defaults={'category':category,'mode':mode,'level':level,'price':price,'schedule':schedule,'description':'دوره نمونه برای بررسی سامانه آموزشگاه زبان پل. محتوای نهایی و برنامه توسط آموزشگاه تعیین می‌شود.','syllabus':'واژگان و کاربرد در موقعیت‌های واقعی\nگرامر در گفت‌وگو\nتمرین درک مطلب و بازخورد استاد','teacher':people['teacher'],'published':True,'start_date':timezone.localdate()+timedelta(days=7)})
            for j in range(3):
                Lesson.objects.get_or_create(course=c,title=f'جلسه {j+1}',defaults={'starts':timezone.now()+timedelta(days=(j-1)*3,hours=2),'completed':j==0})
            if i==0:
                Enrollment.objects.get_or_create(student=people['student'],course=c)
                Order.objects.get_or_create(student=people['student'],course=c,defaults={'amount':price,'status':'paid','reference':'DEMO-NOT-A-REAL-PAYMENT'})
                Grade.objects.get_or_create(student=people['student'],course=c,title='تمرین نمونه درس اول',defaults={'score':86,'feedback':'پیشرفت خوب در کاربرد واژگان؛ روی ساختار جمله بیشتر تمرین کن.'})
        Message.objects.get_or_create(sender=people['admin'],audience='all',subject='به فضای آموزشی پل خوش آمدید',defaults={'body':'این اطلاعیه نمونه است. برنامه کلاس و منابع را در بخش کلاس‌های من دنبال کنید.'})
        Ticket.objects.get_or_create(owner=people['student'],subject='درخواست نمونه: برنامه کلاس',defaults={'body':'لطفاً زمان جلسه بعدی را اعلام کنید.'})
        self.stdout.write('Demo data ready. Existing account passwords were not changed.')
