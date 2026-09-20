"""Read-only, public catalogue for the standalone HTML landing page."""
from django.conf import settings
from django.http import JsonResponse
from django.utils.cache import patch_vary_headers
from django.views.decorators.http import require_GET
from .models import Course, User

@require_GET
def catalog(request):
    courses = Course.objects.filter(published=True).order_by('id')
    teachers = User.objects.filter(role='teacher', is_active=True, teaching__published=True).distinct()
    response = JsonResponse({
        'source': 'pol-public-v1',
        'demo': settings.POL_DEMO,
        'courses': [{
            'id': str(c.pk), 'title': c.title, 'category': c.category,
            'categoryLabel': c.get_category_display(), 'level': c.level,
            'mode': c.mode, 'sessions': c.total_sessions, 'price': c.price,
            'schedule': c.schedule, 'description': c.description,
            'syllabus': [line.strip() for line in c.syllabus.splitlines() if line.strip()],
            'serverPath': f'/courses/{c.pk}/',
        } for c in courses],
        'teachers': [{
            'name': t.get_full_name() or 'مدرس دوره‌های انگلیسی',
            'specialty': 'آموزش انگلیسی در پل', 'sample': settings.POL_DEMO,
        } for t in teachers],
    }, json_dumps_params={'ensure_ascii': False})
    allowed = getattr(settings, 'POL_SITE_ORIGIN', '').rstrip('/')
    if allowed and request.headers.get('Origin') == allowed:
        response['Access-Control-Allow-Origin'] = allowed
    patch_vary_headers(response, ['Origin'])
    response['Cache-Control'] = 'public, max-age=60'
    return response
