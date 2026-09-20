/* Pol Language Center — no network requests, secrets or account storage. */
(function () {
  'use strict';
  const QUESTIONS = /*__QUESTION_DATA__*/;
  const LEVELS = ['A1', 'A2', 'B1', 'B2', 'C1'];
  const fa = value => new Intl.NumberFormat('fa-IR').format(value);
  const esc = value => String(value ?? '').replace(/[&<>"']/g, x => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[x]));
  const normalize = value => String(value || '').normalize('NFKC').replace(/ي/g, 'ی').replace(/ك/g, 'ک').replace(/[\u200c\u200d]/g, ' ').trim().toLowerCase();
  function filterCourses(courses, query, mode, category) {
    const q = normalize(query);
    return courses.filter(c => (!q || normalize(c.title + ' ' + c.description + ' ' + c.categoryLabel + ' ' + c.level).includes(q)) && (!mode || mode === c.mode) && (!category || category === c.category));
  }
  function nextQuestion(answers) {
    const used = new Set(answers.map(a => a.q));
    let difficulty = 1;
    if (answers.length) {
      const last = answers[answers.length - 1];
      difficulty = Math.max(0, Math.min(4, QUESTIONS[last.q][0] + (last.choice === QUESTIONS[last.q][3] ? 1 : -1)));
    }
    const candidates = QUESTIONS.map((q, i) => i).filter(i => !used.has(i));
    candidates.sort((a, b) => Math.abs(QUESTIONS[a][0] - difficulty) - Math.abs(QUESTIONS[b][0] - difficulty) || a - b);
    return candidates[0];
  }
  function placementResult(answers) {
    const correct = answers.filter(a => QUESTIONS[a.q] && a.choice === QUESTIONS[a.q][3]).map(a => QUESTIONS[a.q][0]);
    let band = 0;
    for (let i = 0; i < 5; i++) if (correct.filter(d => d >= i).length >= 2) band = i;
    return {score: answers.length ? Math.round(correct.length / answers.length * 100) : 0, level: LEVELS[band], correct: correct.length};
  }
  function backendOrigin(value, currentHost) {
    if (!value) return '';
    try {
      const url = new URL(value);
      const local = ['localhost', '127.0.0.1', '[::1]'];
      const protocolAllowed = url.protocol === 'https:' || (url.protocol === 'http:' && local.includes(url.hostname) && (!currentHost || local.includes(currentHost)));
      if (!protocolAllowed || url.username || url.password || url.pathname !== '/' || url.search || url.hash) return '';
      return url.origin;
    } catch (_) { return ''; }
  }
  function coursePath(value) { return typeof value === 'string' && /^\/courses\/\d+\/$/.test(value) ? value : '/courses/'; }
  const logic = {QUESTIONS, LEVELS, normalize, filterCourses, nextQuestion, placementResult, backendOrigin, coursePath};
  if (typeof module !== 'undefined' && module.exports) module.exports = logic;
  if (typeof document === 'undefined') return;

  const config = window.POL_CONFIG || {};
  let courses = Array.isArray(config.courses) ? config.courses : [];
  const origin = backendOrigin(config.backendOrigin, location.hostname);
  let sample = config.sampleMode !== false;
  const $ = selector => document.querySelector(selector);
  const $$ = selector => Array.from(document.querySelectorAll(selector));
  const modeName = mode => mode === 'onsite' ? 'حضوری' : 'آنلاین';
  let answers = [], currentQuestion = 0, activeRole = 'student';

  function openDialog(id) {
    $$('dialog[open]').forEach(d => d.close());
    const d = document.getElementById(id);
    d.showModal();
    document.body.classList.add('modal-open');
  }
  $$('dialog').forEach(d => {
    d.addEventListener('close', () => { if (!$('dialog[open]')) document.body.classList.remove('modal-open'); });
    d.addEventListener('click', event => {
      const r = d.getBoundingClientRect();
      if (event.target === d && (event.clientX < r.left || event.clientX > r.right || event.clientY < r.top || event.clientY > r.bottom)) d.close();
    });
  });
  function goBackend(path) {
    const allowed = /^\/(?:login|signup|dashboard|classes|records|orders|messages|tickets|placement|courses)\/(?:\d+\/)?$|^\/auth\/google\/$|^\/manage\/(?:courses|users|security)\/$/;
    if (origin && allowed.test(path)) { location.assign(origin + path); return; }
    showAccess();
  }
  function showAccess() {
    $('#access-live').hidden = !origin;
    $('#access-contact').hidden = !!origin;
    $('#google-link').hidden = !(origin && config.googleEnabled);
    $('#access-demo').hidden = !sample;
    $('#access-message').textContent = origin ? 'برای دیدن کلاس‌ها، منابع و روند پیشرفت، وارد حساب خودت شو. استادان و مدیران نیز از همین بخش وارد پنل متناسب با حسابشان می‌شوند.' : 'ثبت‌نام آنلاین هنوز فعال نشده است. برای هماهنگی ثبت‌نام، اطلاعات تماس آموزشگاه را بررسی کن.';
    openDialog('access-dialog');
  }
  function card(c) {
    const featured = c.category === 'ielts';
    return `<article class="card course-card ${featured ? 'course-featured' : ''}"><div class="course-top"><span class="badge ${featured ? 'gold-badge' : 'violet'}">${esc(c.categoryLabel)}</span><span class="course-code" lang="en" dir="ltr">EN <small>${esc(c.level)}</small></span></div><div class="card-body"><h3>${esc(c.title)}</h3><p class="course-description">${esc(c.description)}</p><div class="course-facts"><span>${fa(c.sessions)} جلسه · ${modeName(c.mode)}</span><span>${esc(c.level)}</span></div><div class="card-bottom"><strong class="money">${fa(c.price)} <small>تومان</small></strong><button class="course-action" data-course="${esc(c.id)}" aria-label="جزئیات ${esc(c.title)}">جزئیات دوره ←</button></div></div></article>`;
  }
  function renderCourses() {
    const list = filterCourses(courses, $('#course-search').value, $('#course-mode').value, $('#course-category').value);
    $('#course-list').innerHTML = list.length ? list.map(card).join('') : '<div class="empty-state"><p>دوره‌ای با این جست‌وجو پیدا نشد.</p><button class="btn secondary" data-reset-filters>نمایش همه دوره‌ها</button></div>';
    $('#course-count').textContent = `${fa(list.length)} دوره از ${fa(courses.length)} دوره`;
  }
  ['course-search', 'course-mode', 'course-category'].forEach(id => document.getElementById(id).addEventListener(id === 'course-search' ? 'input' : 'change', renderCourses));
  function showCourse(id) {
    const c = courses.find(c => c.id === id);
    if (!c) return;
    $('#course-dialog-title').textContent = c.title;
    $('#course-detail').innerHTML = `<div class="course-detail-grid"><div><div class="actions"><span class="badge violet">${esc(c.level)}</span><span class="badge">${modeName(c.mode)}</span></div><p>${esc(c.description)}</p><h3>در این دوره چه یاد می‌گیری؟</h3><ul>${(c.syllabus || []).map(t => '<li>' + esc(t) + '</li>').join('')}</ul><p class="sample-note">${sample ? 'برنامه و شهریه این طرح نمونه‌اند؛ جزئیات نهایی باید توسط آموزشگاه تأیید شوند.' : 'جزئیات نهایی، ظرفیت و شهریه را در سامانه ثبت‌نام بررسی کن.'}</p></div><aside class="course-summary"><dl><div><dt>تعداد جلسات</dt><dd>${fa(c.sessions)} جلسه</dd></div><div><dt>نوع برگزاری</dt><dd>${modeName(c.mode)}</dd></div><div><dt>سطح دوره</dt><dd dir="ltr">${esc(c.level)}</dd></div><div><dt>برنامه</dt><dd>${esc(c.schedule)}</dd></div></dl><div class="money">${fa(c.price)} <small>تومان</small></div><button class="btn gold" data-enroll="${esc(c.id)}">ادامه ثبت‌نام ←</button><p class="sample-note">ثبت‌نام پس از تأیید پرداخت و وجود ظرفیت نهایی می‌شود.</p></aside></div>`;
    openDialog('course-dialog');
  }
  function showPlacement() {
    $('#placement-content').innerHTML = '<div class="placement-intro"><span class="badge violet">حدود ۵ تا ۸ دقیقه</span><h3>قبل از انتخاب دوره، نقطه شروع را پیدا کن.</h3><ol><li>به ۱۲ پرسش گرامر، واژگان و درک مطلب پاسخ می‌دهی.</li><li>سختی پرسش بعدی با پاسخ قبلی تنظیم می‌شود.</li><li>نتیجه صرفاً پیشنهاد اولیه است و مدرک یا ارزیابی معتبر CEFR نیست؛ شنیدن و صحبت‌کردن را نمی‌سنجد.</li></ol></div><p class="sample-note">پاسخ‌ها فقط تا زمان بازبودن این صفحه نگه داشته می‌شوند و به حساب دانشجویی ارسال نمی‌شوند.</p><div class="actions"><button class="btn gold" id="test-start">شروع تعیین سطح ←</button><button class="btn secondary" data-backend="/placement/">تعیین سطح در حساب کاربری</button></div>';
    openDialog('placement-dialog');
  }
  function renderQuestion() {
    if (answers.length >= 12) { renderResult(); return; }
    currentQuestion = nextQuestion(answers);
    const question = QUESTIONS[currentQuestion];
    $('#placement-content').innerHTML = `<div class="test-progress-head"><span>پرسش ${fa(answers.length + 1)} از ۱۲</span><span>یک پاسخ را انتخاب کن</span></div><div class="test-progress" role="progressbar" aria-label="پیشرفت آزمون" aria-valuenow="${answers.length}" aria-valuemin="0" aria-valuemax="12"><div style="width:${answers.length / 12 * 100}%"></div></div><form id="question-form"><h3 class="test-question" id="test-question" tabindex="-1" lang="en" dir="ltr">${esc(question[1])}</h3><fieldset class="test-choices" aria-labelledby="test-question" dir="ltr">${question[2].map((option, i) => `<label class="test-choice"><input type="radio" name="answer" value="${i}" required><span>${esc(option)}</span></label>`).join('')}</fieldset><div class="actions"><button class="btn gold" type="submit" id="test-next" disabled>${answers.length === 11 ? 'دیدن نتیجه ←' : 'پرسش بعدی ←'}</button><button class="btn secondary" type="button" id="test-back" ${answers.length ? '' : 'disabled'}>پرسش قبلی</button></div></form>`;
    $('#test-question').focus();
    $('#question-form').addEventListener('change', () => { $('#test-next').disabled = false; });
    $('#question-form').addEventListener('submit', event => {
      event.preventDefault();
      const selected = $('#question-form input:checked');
      if (!selected) return;
      answers.push({q:currentQuestion, choice:Number(selected.value)});
      renderQuestion();
    });
  }
  function renderResult() {
    const result = placementResult(answers);
    $('#placement-content').innerHTML = `<div class="test-result"><p class="dialog-eyebrow">پیشنهاد اولیه مسیر یادگیری</p><div class="result-level" lang="en">${result.level}</div><h3 tabindex="-1" id="result-heading">یک قدم به انتخاب مسیر نزدیک‌تر شدی.</h3><p>${fa(result.correct)} پاسخ درست از ۱۲ پرسش · امتیاز ${fa(result.score)} از ۱۰۰</p><div class="levels-track">${LEVELS.map(l => `<span class="${l === result.level ? 'active' : ''}">${l}</span>`).join('')}</div><p class="sample-note">این نتیجه موقت و بر پایه چند پرسش کوتاه است. سطح نهایی را با ارزیابی استاد، به‌ویژه در مهارت گفتاری و شنیداری، مشخص کن. نتیجه این صفحه در سامانه آموزشی ثبت نشده است.</p><div class="actions"><a class="btn gold" href="#courses" data-show-courses>مشاهده دوره‌ها</a><button class="btn secondary" id="test-start">تکرار آزمون</button><button class="btn secondary" data-backend="/placement/">تعیین سطح در حساب</button></div></div>`;
    $('#result-heading').focus();
  }

  const roles = {
    student:{title:'دانشجو',greeting:'سلام، زبان‌آموز پل',intro:'برنامه کلاس‌ها، منابع و پیشرفتت را یک‌جا دنبال کن.',metrics:[['A2','سطح در حال یادگیری'],['۶ از ۱۶','جلسه تکمیل‌شده'],['۸۷٪','میانگین تمرین‌ها']],tabs:[['overview','نمای کلی'],['classes','کلاس‌های من'],['records','کارنامه'],['messages','پیام‌ها و پشتیبانی']]},
    teacher:{title:'استاد',greeting:'فضای تدریس و همراهی',intro:'کلاس، حضور و غیاب و بازخورد آموزشی را مدیریت کن.',metrics:[['۳','کلاس در این ترم'],['۲۸','زبان‌آموز'],['۲','جلسه امروز']],tabs:[['overview','نمای کلی'],['classes','کلاس‌ها و حضور'],['records','ارزیابی دانشجویان'],['messages','پیام‌ها و پشتیبانی']]},
    admin:{title:'مدیریت',greeting:'نمای کلی آموزشگاه',intro:'دوره‌ها، کاربران، شهریه‌ها و درخواست‌ها در یک نگاه.',metrics:[['۳۶','ثبت‌نام این ترم'],['۹۲٫۴','دریافتی نمونه · میلیون تومان'],['۴','تیکت باز']],tabs:[['overview','نمای کلی'],['classes','دوره‌ها و کاربران'],['records','گزارش مالی'],['messages','ارتباطات و امنیت']]}
  };
  const row = (a,b,success=false) => `<div class="portal-row"><span>${a}</span><span class="portal-pill ${success ? 'success' : ''}">${b}</span></div>`;
  const widget = (title,content) => `<div class="portal-widget"><h4>${title}</h4>${content}</div>`;
  const table = (headers,rows) => `<div style="overflow:auto"><table class="portal-table"><thead><tr>${headers.map(h=>'<th>'+h+'</th>').join('')}</tr></thead><tbody>${rows.map(r=>'<tr>'+r.map(c=>'<td>'+c+'</td>').join('')+'</tr>').join('')}</tbody></table></div>`;
  function portalContent(role,tab) {
    if (tab === 'overview') {
      if (role === 'student') return widget('مسیر یادگیری انگلیسی', '<div class="levels-track"><span>A1</span><span class="active">A2</span><span>B1</span><span>B2</span><span>C1</span></div><div class="portal-progress"><span></span></div><p>۶ جلسه از ۱۶ جلسه این ترم تکمیل شده است.</p>') + widget('برنامه پیش رو',row('انگلیسی عمومی · جلسه هفتم','دوشنبه · ۱۷:۰۰')+row('تمرین واژگان فصل سوم','در انتظار تحویل'));
      if (role === 'teacher') return widget('کلاس‌های پیش رو',row('انگلیسی عمومی A1 · ۱۰ زبان‌آموز','حضوری · ۱۷:۰۰')+row('مکالمه B1 · ۸ زبان‌آموز','آنلاین · ۱۸:۰۰'))+widget('پیگیری آموزشی',row('تمرین‌های منتظر بازخورد','۶ تمرین')+row('حضور و غیاب آخرین جلسه','ثبت‌شده',true));
      return widget('وضعیت عملیات',row('دوره‌های فعال','۳ دوره',true)+row('سفارش‌های منتظر پرداخت','۵ سفارش')+row('تیکت‌های نیازمند پاسخ','۴ درخواست'))+widget('فعالیت اخیر',row('ثبت‌نام نمونه در مکالمه','۱۰ دقیقه پیش')+row('ثبت حضور و غیاب کلاس A1','۲۰ دقیقه پیش'));
    }
    if (tab === 'classes') {
      if (role === 'admin') return widget('مدیریت دوره‌ها',table(['دوره','نوع','سطح','وضعیت'],[['انگلیسی عمومی','حضوری','A1','فعال'],['مکالمه','آنلاین','B1','فعال'],['آیلتس','آنلاین','B2','فعال']]))+widget('دسترسی کاربران',row('دانشجو','کلاس، کارنامه و سفارش خود')+row('استاد','کلاس‌های واگذارشده')+row('مدیر','مدیریت کاربران و عملیات'));
      if (role === 'teacher') return widget('حضور و غیاب · جلسه هفتم',table(['زبان‌آموز نمونه','وضعیت حضور','تمرین'],[['زبان‌آموز ۱','حاضر','تحویل‌شده'],['زبان‌آموز ۲','حاضر','در انتظار'],['زبان‌آموز ۳','غایب','تحویل‌شده']]))+widget('ابزارهای کلاس',row('لینک کلاس، ضبط جلسه و منابع','قابل مدیریت در سامانه'));
      return widget('انگلیسی عمومی · A2',row('برنامه جلسات','شنبه و دوشنبه · ۱۷:۰۰')+row('منابع این هفته','واژگان و تمرین شنیداری')+row('پیشرفت ترم','۶ جلسه تکمیل‌شده',true))+widget('کلاس آنلاین',row('ورود به جلسه و دیدن منابع','پس از ورود به حساب'));
    }
    if (tab === 'records') {
      if (role === 'admin') return widget('سفارش‌های نمونه · تومان',table(['شماره','دوره','مبلغ','وضعیت'],[['POL-1001','انگلیسی عمومی','۲٬۴۰۰٬۰۰۰','پرداخت‌شده'],['POL-1002','آیلتس','۳٬۸۰۰٬۰۰۰','در انتظار'],['POL-1003','مکالمه','۲٬۹۰۰٬۰۰۰','پرداخت‌شده']]))+widget('گزارش‌ها',row('خروجی مالی CSV','در سامانه مدیریت'));
      if (role === 'teacher') return widget('ارزیابی نمونه دانشجویان',table(['زبان‌آموز','تمرین','میان‌ترم','بازخورد'],[['زبان‌آموز ۱','۹۰','۸۵','پیشرفت مناسب'],['زبان‌آموز ۲','۸۰','۷۸','تمرین مکالمه'],['زبان‌آموز ۳','۸۸','۹۰','پیشرفت مناسب']]));
      return widget('کارنامه این ترم',table(['ارزیابی','امتیاز از ۱۰۰','وضعیت'],[['تمرین‌های کلاسی','۸۷','ثبت‌شده'],['میان‌ترم','۸۵','ثبت‌شده'],['پایان‌ترم','—','برگزار نشده']]))+widget('نتیجه تعیین سطح',row('پیشنهاد اولیه A2','نیازمند ارزیابی گفتاری'));
    }
    if (role === 'admin') return widget('درخواست‌های نمونه',row('تیکت تغییر ساعت کلاس','باز')+row('پرسش درباره شهریه','پاسخ داده شد',true))+widget('ثبت رویدادهای امنیتی',row('ورود مدیر نمونه','موفق',true)+row('تغییر نقش کاربر نمونه','ثبت در سوابق'))+widget('ارتباطات',row('پیام گروهی و ارتباط با کارکنان','در پنل مدیریت'));
    return widget('پیام‌های نمونه',row('یادآوری برنامه جلسه بعد','آموزشگاه پل')+row('منابع جدید کلاس اضافه شد','واحد آموزش'))+widget('پشتیبانی',row('درخواست بررسی برنامه کلاس','در حال پیگیری'));
  }
  function renderPortal(tab='overview') {
    const role = roles[activeRole];
    $('#portal-title').textContent = 'نمونه پنل ' + role.title;
    $('#portal-nav').innerHTML = `<strong>آموزشگاه زبان پل</strong>${role.tabs.map(([id,label])=>`<button data-portal-tab="${id}" aria-pressed="${id===tab}">${label}</button>`).join('')}`;
    $('#portal-main').innerHTML = `<div class="portal-toolbar"><button class="btn secondary" data-open="access">انتخاب پنل</button><button class="btn gold" data-backend="/dashboard/">ورود به حساب واقعی</button></div><h3>${role.greeting}</h3><p>${role.intro}</p>${tab==='overview' ? `<div class="portal-metrics">${role.metrics.map(([v,l])=>`<div class="portal-metric"><strong>${v}</strong><small>${l}</small></div>`).join('')}</div>` : ''}${portalContent(activeRole,tab)}`;
  }
  function hydrate() {
    renderCourses();
    $('#hero-course-count').textContent = fa(courses.length);
    $$('[data-sample-note]').forEach(n => { n.hidden = !sample; });
    const featured = courses.find(c=>c.category==='ielts') || courses[0];
    if (featured) {
      const fc = $('.feature-content');
      fc.innerHTML = `<span class="badge violet">دوره پیشنهادی</span><h2>${esc(featured.title)}</h2><p>${esc(featured.description)}</p><ul class="feature-list"><li>${fa(featured.sessions)} جلسه آموزشی · سطح ${esc(featured.level)}</li><li>${modeName(featured.mode)} · ${esc(featured.schedule)}</li><li>منابع آموزشی و پیگیری پیشرفت در پنل دانشجو</li></ul><div class="actions"><button data-course="${esc(featured.id)}" class="btn gold">جزئیات و ثبت‌نام</button><strong class="money">${fa(featured.price)} <small>تومان</small></strong></div>`;
    } else $('.feature-section').hidden = true;
    const teachers = (config.teachers || []).filter(t => sample || !t.sample);
    $('#teachers').hidden = !teachers.length;
    $$('a[href="#teachers"]').forEach(a=>{a.hidden=!teachers.length;});
    $('.teacher-grid').innerHTML = teachers.map(t=>{
      const portrait = t.sample && /^portrait-(one|two|three|four)$/.test(t.portrait || '') ? `<div class="teacher-photo ${t.portrait}" role="img" aria-label="پرتره ساختگی برای نمایش کارت آموزگار"></div>` : `<div class="teacher-photo teacher-initials" aria-hidden="true">${esc((t.name || '').slice(0,1))}</div>`;
      return `<article class="teacher-card">${portrait}<h3>${esc(t.name)}</h3><p>${esc(t.specialty)}</p>${t.sample?'<span class="demo-profile">پروفایل نمونه</span>':''}</article>`;
    }).join('');
    $('#teacher-section-note').textContent = sample ? 'تصاویر و پروفایل‌های این بخش، نمونه طراحی هستند.' : 'همراهان مسیر یادگیری تو';
    const methods = [];
    const phone = String(config.phone || '').trim();
    if (/^\+?[0-9 ()-]{7,22}$/.test(phone)) methods.push(`<div class="contact-method"><small>تلفن آموزشگاه</small><a href="tel:${esc(phone.replace(/[ ()-]/g,''))}" dir="ltr">${esc(phone)}</a></div>`);
    const email = String(config.email || '').trim();
    if (/^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/.test(email)) methods.push(`<div class="contact-method"><small>ایمیل</small><a href="mailto:${esc(email)}" dir="ltr">${esc(email)}</a></div>`);
    if (config.address) methods.push(`<div class="contact-method"><small>نشانی آموزشگاه</small><span>${esc(config.address)}</span></div>`);
    $('#contact-methods').innerHTML = methods.length ? methods.join('') : '<p class="contact-unset">اطلاعات تماس آموزشگاه به‌زودی در این بخش قرار می‌گیرد.</p>';
    $('#contact-support').hidden = !origin;
  }

  document.addEventListener('click', event => {
    const target = event.target.closest('button,a');
    if (!target) return;
    if (target.hasAttribute('data-close')) { event.preventDefault(); target.closest('dialog').close(); }
    else if (target.dataset.course) { event.preventDefault(); showCourse(target.dataset.course); }
    else if (target.dataset.enroll) { event.preventDefault(); const course = courses.find(c=>c.id===target.dataset.enroll); goBackend(coursePath(course && course.serverPath)); }
    else if (target.dataset.backend) { event.preventDefault(); goBackend(target.dataset.backend); }
    else if (target.dataset.open) { event.preventDefault(); if(target.dataset.open==='placement') showPlacement(); else showAccess(); }
    else if (target.dataset.portal) { event.preventDefault(); activeRole=target.dataset.portal in roles ? target.dataset.portal : 'student'; renderPortal(); openDialog('portal-dialog'); }
    else if (target.dataset.portalTab) { event.preventDefault(); renderPortal(target.dataset.portalTab); }
    else if (target.id === 'test-start') { answers=[]; renderQuestion(); }
    else if (target.id === 'test-back') { answers.pop(); renderQuestion(); }
    else if (target.hasAttribute('data-reset-filters')) { ['course-search','course-mode','course-category'].forEach(id=>{document.getElementById(id).value='';}); renderCourses(); }
    else if (target.hasAttribute('data-contact') || target.hasAttribute('data-show-courses')) { $$('dialog[open]').forEach(d=>d.close()); }
    if (target.closest('#main-nav')) { $('#main-nav').classList.remove('is-open'); $('#nav-toggle').setAttribute('aria-expanded','false'); }
  });
  $('#nav-toggle').addEventListener('click', () => { const state = $('#main-nav').classList.toggle('is-open'); $('#nav-toggle').setAttribute('aria-expanded',String(state)); });
  document.addEventListener('keydown', event => { if(event.key==='Escape') { $('#main-nav').classList.remove('is-open'); $('#nav-toggle').setAttribute('aria-expanded','false'); } });
  hydrate();
  // This request runs only after the owner configures their own panel origin.
  // Public data only: no cookies, tokens, passwords or placement answers.
  if (origin) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 8000);
    fetch(origin + '/api/public/catalog/', {credentials:'omit', mode:'cors', signal:controller.signal})
      .then(response => { if (!response.ok) throw new Error('catalog unavailable'); return response.json(); })
      .then(data => {
        if (data.source !== 'pol-public-v1' || !Array.isArray(data.courses) || !Array.isArray(data.teachers)) throw new Error('invalid catalog');
        if (!data.courses.every(c => typeof c.title === 'string' && typeof c.id === 'string' && Number.isSafeInteger(c.price) && c.price >= 0 && ['onsite','online'].includes(c.mode) && Array.isArray(c.syllabus))) throw new Error('invalid courses');
        courses = data.courses;
        config.teachers = data.teachers;
        sample = data.demo === true;
        hydrate();
        $('#catalog-connection').textContent = 'دوره‌ها و شهریه‌ها از فهرست فعلی آموزشگاه نمایش داده می‌شوند.';
      })
      .catch(() => { $('#catalog-connection').textContent = 'به‌روزرسانی فهرست آنلاین فعلاً در دسترس نیست؛ جزئیات قطعی را در سامانه ثبت‌نام بررسی کن.'; })
      .finally(() => clearTimeout(timeout));
  }
})();
