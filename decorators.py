import datetime
from functools import wraps
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone


def authentication_required(function=None):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            session = request.session
            if session.get("provider") \
                    and session.get("patient_id") \
                    and session.get("patient") \
                    and session.get("access_token") \
                    and session.get("expiration"):
                expiration = session.get("expiration")
                if isinstance(expiration, datetime.datetime) and expiration > timezone.now():
                    return view_func(request, *args, **kwargs)
            # Clear the session if authentication failed.
            request.session.flush()
            return HttpResponseRedirect(reverse("pisces:index"))
        return _wrapped_view
    if function:
        return decorator(function)
    return decorator
