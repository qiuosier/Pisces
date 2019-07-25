from django.http import HttpResponseRedirect


def authentication_required(function=None):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            session = request.session
            if session.get("endpoint") and session.get("patient") and session.get("access_token"):
                return view_func(request, *args, **kwargs)
            return HttpResponseRedirect("/")
        return _wrapped_view
    if function:
        return decorator(function)
    return decorator