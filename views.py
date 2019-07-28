import json
import os
import requests
import re
import ast
import logging
from lxml import etree
from django.conf import settings
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from rhythm.private import EPIC_TEST_ID, EPIC_CLIENT_ID, EPIC_REDIRECT_URL
from Pisces.decorators import authentication_required
from Pisces import endpoints
logger = logging.getLogger(__name__)


def exchange_token(provider, authorization_code):
    token_endpoint = endpoints.get_endpoint(provider, "token")
    client_id = EPIC_CLIENT_ID if provider != "Demo" else EPIC_TEST_ID
    data = {
        "grant_type": "authorization_code",
        "code": authorization_code,
        "redirect_uri": EPIC_REDIRECT_URL,
        "client_id": client_id
    }
    response = requests.post(token_endpoint, data)
    token_json = response.json()
    return token_json


def get_patient_info(request):
    if not request.session.get("patient"):
        patient_id = request.session.get("patient_id")
        api = endpoints.initialize_api(request)
        try:
            response = api.get("Patient/%s" % patient_id)
        except Exception as ex:
            request.session["errors"] = "%s: %s" % (type(ex), str(ex))
            return None
        if response.status_code != 200:
            request.session["errors"] = "Failed to get patient data.\n Response Code: %s.\n %s" % (
                response.status_code, 
                response.content
            )
            return None
        request.session["patient"] = response.json()
    return request.session.get("patient")


def logout(request):
    request.session.flush()
    return redirect("pisces:home")


def index(request):
    authorization_code = request.GET.get("code")
    provider = request.session.get("provider")
    if authorization_code and provider:
        token_json = exchange_token(provider, authorization_code)
        request.session["access_token"] = token_json.get("access_token")
        request.session["patient_id"] = token_json.get("patient")
        if request.session["access_token"] and request.session["patient_id"]:
            return redirect("pisces:home")
        return HttpResponse("Authentication Failed.")
    providers = endpoints.load_providers()
    # Index page displays and clear the errors.
    errors = request.session.pop("errors", None)
    return render(request, "index.html", {
        "title": "Pisces",
        "providers": providers,
        "top_providers": ["Demo", "Duke Health"],
        "errors": errors,
    })


def authenticate(request):
    provider = request.GET.get("provider")
    request.session["provider"] = provider
    client_id = EPIC_CLIENT_ID if provider != "Demo" else EPIC_TEST_ID
    if provider == "Demo":
        request.session["access_token"] = "X"
        request.session["patient_id"] = "Tbt3KuCY0B5PSrJvCu2j-PlK.aiHsu2xUjUM8bWpetXoB"
        request.session["patient"] = get_patient_info(request)
        return redirect("pisces:home")
    authorize_endpoint = endpoints.get_endpoint(provider, "authorize")
    if not authorize_endpoint:
        return HttpResponse("Healthcare provider %s is currently not supported." % provider)
        
    redirect_url = "%s?response_type=code&client_id=%s&redirect_uri=%s" % (
        authorize_endpoint,
        client_id,
        EPIC_REDIRECT_URL
    )
    return HttpResponseRedirect(redirect_url)


@authentication_required
def home(request):
    patient = get_patient_info(request)
    resources = [
        {
            "name": "Laboratory Results",
            "link": "observations"
        }
    ]
    return render(request, "home.html", {
        "title": "Your Data",
        "patient": patient,
        "resources": resources,
    })


@authentication_required
def observations(request):
    patient_id = request.session.get("patient_id")
    api = endpoints.initialize_api(request)
    response = api.get("Observation", patient=patient_id, category="Laboratory")
    print(response.content)

    entries = response.json().get("entry")
    return render(request, "observations.html", {
        "title": "Observations",
        "entries": entries,
        "total": response.json().get("total")
    })
