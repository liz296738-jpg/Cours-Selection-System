from .models import SiteSetting


def site_context(request):
    try:
        setting = SiteSetting.load()
    except Exception:
        setting = None
    return {"global_setting": setting}
