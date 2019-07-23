import json
import os
from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse


def index(request):
    with open(os.path.join(settings.BASE_DIR, "EpicEndpoints.json")) as endpoint_json:
        providers = json.load(endpoint_json).get("Entries")
    return render(request, "home.html", {
        "title": "Pisces by Qiu",
        "providers": providers
    })
