#!/usr/bin/env python3
"""Build the HTML edition using only Python's standard library.

Run from any directory: python source/build.py
Outputs public_html/ and Pol-Language.html at the package root.
"""
import base64
import html
import json
import mimetypes
import re
import shutil
from pathlib import Path

SOURCE = Path(__file__).resolve().parent
ROOT = SOURCE.parent
PUBLIC = ROOT / 'public_html'
ASSETS = SOURCE / 'assets'

def data_uri(path):
    mime = {'.ttf':'font/ttf', '.svg':'image/svg+xml'}.get(path.suffix, mimetypes.guess_type(path.name)[0] or 'application/octet-stream')
    return 'data:' + mime + ';base64,' + base64.b64encode(path.read_bytes()).decode('ascii')

def json_for_script(value):
    return json.dumps(value, ensure_ascii=False, indent=2).replace('</', '<\\/').replace('\u2028','\\u2028').replace('\u2029','\\u2029')

def fa_number(value):
    return f'{int(value):,}'.translate(str.maketrans('0123456789,','۰۱۲۳۴۵۶۷۸۹٬'))

def card_markup(c):
    e=lambda key:html.escape(str(c.get(key,'')),quote=True)
    featured=c.get('category')=='ielts'
    return ('<article class="card course-card '+('course-featured' if featured else '')+'"><div class="course-top"><span class="badge '+('gold-badge' if featured else 'violet')+'">'+e('categoryLabel')+'</span><span class="course-code" lang="en" dir="ltr">EN <small>'+e('level')+'</small></span></div><div class="card-body"><h3>'+e('title')+'</h3><p class="course-description">'+e('description')+'</p><div class="course-facts"><span>'+fa_number(c['sessions'])+' جلسه · '+('حضوری' if c['mode']=='onsite' else 'آنلاین')+'</span><span>'+e('level')+'</span></div><div class="card-bottom"><strong class="money">'+fa_number(c['price'])+' <small>تومان</small></strong><button class="course-action" data-course="'+e('id')+'">جزئیات دوره ←</button></div></div></article>')

def build():
    config = json.loads((SOURCE/'site-config.json').read_text())
    questions = json.loads((SOURCE/'questions.json').read_text())
    PUBLIC.mkdir(exist_ok=True)
    shutil.copytree(ASSETS, PUBLIC/'assets', dirs_exist_ok=True)
    css = (ASSETS/'site.css').read_text() + '\n' + (SOURCE/'html-edition.css').read_text()
    (PUBLIC/'assets/site.css').write_text(css)
    js = (SOURCE/'site.js').read_text().replace('/*__QUESTION_DATA__*/',json_for_script(questions))
    (PUBLIC/'assets/site.js').write_text(js)
    config_js = '// Public presentation settings only. Never put secrets here.\nwindow.POL_CONFIG = ' + json_for_script(config) + ';\n'
    (PUBLIC/'site-config.js').write_text(config_js)
    page = (SOURCE/'home-base.html').read_text()
    page = re.sub(r'<div class="preview-toolbar">.*?</div>', '', page, count=1)
    page = page.replace('<body>', '<body id="top"><a href="#main-content" class="skip-link">رفتن به محتوای اصلی</a>')
    page = page.replace('<main class="public-home">', '<main class="public-home" id="main-content">')
    page = page.replace('<nav class="nav"', '<button class="nav-toggle" id="nav-toggle" aria-expanded="false" aria-controls="main-nav">منو ☰</button><nav id="main-nav" class="nav"')
    page = page.replace('</nav>', '<a class="mobile-access" href="#access-dialog" data-open="access">ورود / ثبت‌نام</a><a class="mobile-access" href="#placement-dialog" data-open="placement">تعیین سطح</a></nav>',1)
    rewrites = {
        'index.html':'#top', 'index.html#teachers':'#teachers','index.html#about':'#about','index.html#questions':'#questions','index.html#contact':'#contact',
        'courses.html':'#courses', 'unavailable.html':'#contact',
    }
    for old,new in rewrites.items(): page=page.replace('href="'+old+'"','href="'+new+'"')
    for f in ('login.html','signup.html'): page=page.replace('href="'+f+'"','href="#access-dialog" data-open="access"')
    page=page.replace('href="placement.html"','href="#placement-dialog" data-open="placement"')
    page=page.replace('href="student-tickets.html"','href="#access-dialog" data-backend="/tickets/"')
    for f,c in [('course.html','general'),('course-2.html','ielts'),('course-3.html','conversation')]: page=page.replace('href="'+f+'"','href="#course-dialog" data-course="'+c+'"')
    page=page.replace('<strong>3</strong>','<strong id="hero-course-count">۳</strong>',1)
    page=page.replace('width="1024" height="1024"','width="1254" height="1254"')
    page=page.replace('<section class="catalog-section">','<section class="catalog-section" id="courses">')
    filters = '<div class="catalog-filters"><label>جست‌وجوی دوره<input type="search" id="course-search" placeholder="مثلاً مکالمه یا آیلتس…" autocomplete="off"></label><label>نوع برگزاری<select id="course-mode"><option value="">همه کلاس‌ها</option><option value="onsite">حضوری</option><option value="online">آنلاین</option></select></label><label>گروه آموزشی<select id="course-category"><option value="">همه دوره‌ها</option><option value="general">انگلیسی عمومی</option><option value="ielts">آیلتس</option><option value="conversation">مکالمه</option></select></label></div><p class="sample-note" data-sample-note>اطلاعات دوره‌ها، برنامه و شهریه در این طرح نمونه‌اند و نیاز به تأیید آموزشگاه دارند.</p><p class="result-count" id="course-count" role="status" aria-live="polite"></p>'
    page=page.replace('<div class="grid">',filters+'<p class="sample-note" id="catalog-connection" role="status"></p><div class="grid" id="course-list">',1)
    page=re.sub(r'(<div class="grid" id="course-list">).*?(</div></div></section>)',lambda m:m.group(1)+''.join(card_markup(c) for c in config['courses'])+m.group(2),page,count=1,flags=re.S)
    page=page.replace('<p>چیدمان معرفی استادان؛ تصاویر و پروفایل‌ها نمونه طراحی هستند.</p>','<p id="teacher-section-note">تصاویر و پروفایل‌های این بخش، نمونه طراحی هستند.</p>')
    featured=next((c for c in config['courses'] if c['category']=='ielts'),None)
    if featured:
        page=page.replace('دوره نمونه برای بررسی سامانه آموزشگاه زبان پل. محتوای نهایی و برنامه توسط آموزشگاه تعیین می‌شود.',html.escape(featured['description']))
    page=page.replace('<footer class="footer" id="contact">','<footer class="footer">')
    contact = '<section class="contact-section" id="contact"><div class="wrap"><div class="contact-card"><div><span class="eyebrow">در ارتباط باشیم</span><h2>برای قدم بعدی، همراهت هستیم.</h2><p>درباره انتخاب دوره، زمان کلاس‌ها یا ثبت‌نام سؤال داری؟ با آموزشگاه پل در ارتباط باش.</p><a class="text-link" id="contact-support" href="#access-dialog" data-backend="/tickets/" hidden>پشتیبانی در حساب کاربری ←</a></div><div class="contact-methods" id="contact-methods"><p class="contact-unset">اطلاعات تماس آموزشگاه به‌زودی در این بخش قرار می‌گیرد.</p></div></div></div></section>'
    page=page.replace('</main>',contact+'</main>')
    page=page.replace('<a href="#contact">ارتباط با آموزشگاه ←</a>','<a href="#contact">ارتباط با آموزشگاه ←</a><br><button class="footer-portal-link" data-open="access" data-sample-note>آشنایی با پنل‌ها</button>')
    page=page.replace('static/pol/','assets/')
    page=page.replace('</head>','<link rel="license" href="assets/OFL.txt"></head>')
    page=page.replace('<title>آموزشگاه زبان پل</title>','<title>آموزشگاه زبان پل | دوره‌های انگلیسی حضوری و آنلاین</title><meta name="theme-color" content="#140f27"><meta property="og:type" content="website"><meta property="og:title" content="آموزشگاه زبان پل"><meta property="og:description" content="پلی به دنیای انگلیسی؛ دوره‌های حضوری و آنلاین و تعیین سطح اولیه">')
    page=page.replace('</body>',(SOURCE/'dialogs.html').read_text()+'<noscript><div class="no-script">برای استفاده از جست‌وجوی دوره‌ها، تعیین سطح و پنجره‌های سایت، JavaScript مرورگر را فعال کن.</div></noscript><script src="site-config.js"></script><script src="assets/site.js"></script></body>')
    assert 'preview-toolbar' not in page
    assert 'unavailable.html' not in page
    (PUBLIC/'index.html').write_text(page)

    fonts=(ASSETS/'fonts.css').read_text()
    inlined_css=re.sub(r'@import\s+url\(["\']?fonts.css["\']?\)\s*;',lambda m:fonts,css)
    if '@font-face' not in inlined_css: inlined_css=fonts+'\n'+inlined_css
    def css_asset(match):
        name=match.group(1).strip('\"\' ')
        if name.startswith(('data:','#','http:','https:')): return match.group(0)
        path=ASSETS/name
        if not path.is_file(): raise FileNotFoundError(path)
        return 'url("'+data_uri(path)+'")'
    inlined_css=re.sub(r'url\(([^)]+)\)',css_asset,inlined_css)
    standalone=page.replace('<link rel="stylesheet" href="assets/site.css">','<style>'+inlined_css+'</style>')
    def html_asset(match): return match.group(1)+'="'+data_uri(ASSETS/match.group(2))+'"'
    standalone=re.sub(r'(src|href)="assets/([^\"]+\.(?:png|webp|jpg|svg|ttf|txt))"',html_asset,standalone)
    standalone=standalone.replace('<script src="site-config.js"></script>','<script>'+config_js+'</script>')
    standalone=standalone.replace('<script src="assets/site.js"></script>','<script>'+js+'</script>')
    assert 'href="assets/' not in standalone and 'src="assets/' not in standalone
    assert '@import' not in inlined_css
    (ROOT/'Pol-Language.html').write_text(standalone)
    print('Built public_html/index.html and Pol-Language.html')

if __name__ == '__main__':
    build()
