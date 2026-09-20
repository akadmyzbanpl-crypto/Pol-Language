"""Export read-only pages with generated demo records. Never run on production data."""
import os,re,shutil
from pathlib import Path
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
import django
django.setup()
from django.conf import settings
from django.test import Client,override_settings
from academy.models import User,Course,Order,PlacementResult
if not settings.DEBUG or not settings.POL_DEMO: raise RuntimeError('Demo environment only')
root=Path(__file__).resolve().parent
out=root.parent/'preview';out.mkdir(exist_ok=True)
shutil.copytree(root/'static',out/'static',dirs_exist_ok=True)
client=Client();mapping={}
public={'index.html':'/','courses.html':'/courses/','course.html':'/courses/1/','login.html':'/login/','signup.html':'/signup/','course-2.html':'/courses/2/','course-3.html':'/courses/3/'}
role_routes={'dashboard':'/dashboard/','classes':'/classes/','classroom':'/classes/1/','messages':'/messages/','tickets':'/tickets/','ticket-new':'/tickets/new/','records':'/records/','orders':'/orders/'}
admin_extra={'manage-courses':'/manage/courses/','course-new':'/manage/courses/new/','users':'/manage/users/','security':'/manage/security/','compose':'/messages/new/'}
nav='<div class="preview-toolbar"><span>پیش‌نمایش آفلاین · اطلاعات و تصاویر استادان نمونه‌اند</span><a href="index.html">خانه</a> | <a href="student-dashboard.html">دانشجو</a> | <a href="teacher-dashboard.html">استاد</a> | <a href="admin-dashboard.html">مدیر</a> | <a href="placement.html">تعیین سطح</a></div>'

def export(filename,path,route_map):
    res=client.get(path)
    if res.status_code!=200: raise RuntimeError(f'{path}: {res.status_code}')
    text=res.content.decode()
    text=text.replace('<body>','<body>'+nav)
    text=re.sub(r'<div class="demo">.*?</div>','',text,count=1)
    text=text.replace('href="/static/','href="static/').replace('src="/static/','src="static/')
    text=re.sub(r'<input[^>]+name="csrfmiddlewaretoken"[^>]*>','',text)
    text=re.sub(r'<script[^>]*src="[^"]*(?:live|metrics).js"[^>]*></script>','',text)
    def rewrite(m):
        link=m.group(1)
        if link.startswith('/'):
            path,separator,fragment=link.partition('#')
            return 'href="'+route_map.get(path,'unavailable.html')+(separator+fragment if separator else '')+'"'
        return m.group(0)
    text=re.sub(r'href="([^"]+)"',rewrite,text)
    text=re.sub(r'<form\b[^>]*>', '<form onsubmit="event.preventDefault();alert(\'این نسخه فقط پیش‌نمایش است. برای ثبت اطلاعات، نسخه server را اجرا کنید.\')">',text)
    # Remove links/data routes for active classroom polling in a static snapshot.
    text=text.replace('در حال دریافت وضعیت کلاس…','گفت‌وگوی زنده در نسخه سرور فعال است.')
    text=text.replace('<button id="raise-hand"','<button disabled id="raise-hand"').replace('<button class="btn secondary small" id="chat-control"','<button disabled class="btn secondary small" id="chat-control"')
    (out/filename).write_text(text)

with override_settings(SECURE_SSL_REDIRECT=False):
    base_map={v:k for k,v in public.items()};base_map.update({'/placement/':'placement.html','/dashboard/':'student-dashboard.html','/tickets/':'student-tickets.html'})
    for filename,path in public.items(): export(filename,path,base_map)
    for role in ['student','teacher','admin']:
        client.force_login(User.objects.get(username='demo_'+role))
        paths=dict(role_routes)
        if role=='admin':paths.update(admin_extra)
        if role in ['teacher','admin']:
            for c in Course.objects.exclude(pk=1): paths['classroom-'+str(c.pk)]=f'/classes/{c.pk}/'
        route_map={**base_map,**{v:role+'-'+k+'.html' for k,v in paths.items()}}
        order=Order.objects.filter(student__username='demo_student').first()
        if role in ['student','admin']:
            paths['order']=f'/orders/{order.pk}/';route_map[paths['order']]=role+'-order.html'
        for suffix,path in paths.items(): export(role+'-'+suffix+'.html',path,route_map)
        if role=='student': export('placement.html','/placement/',route_map)
    (out/'unavailable.html').write_text('<!doctype html><html lang="fa" dir="rtl"><meta charset="utf-8"><link rel="stylesheet" href="static/pol/site.css"><title>نسخه نمایشی پل</title><main class="wrap"><section class="test panel"><h1>این بخش به اجرای سرور نیاز دارد</h1><p>فایل راهنمای بسته را برای اجرای نسخه کامل بخوانید. پیش‌نمایش آفلاین فقط برای بررسی ظاهر است.</p><a class="btn" href="index.html">بازگشت به خانه</a></section></main></html>')
print('Exported',len(list(out.glob('*.html'))),'offline pages')
