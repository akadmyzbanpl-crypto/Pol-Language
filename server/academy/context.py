from django.conf import settings

def common(request):
    return {'demo_mode': settings.POL_DEMO,'google_enabled':bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET),'payments_enabled':bool(settings.ZARINPAL_MERCHANT_ID),'school_name':'آموزشگاه زبان پل'}
