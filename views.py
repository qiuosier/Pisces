import json
import os
import requests
import re
import ast
from lxml import etree
from django.conf import settings
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from Aries.web import WebAPI
from rhythm.private import EPIC_TEST_ID, EPIC_CLIENT_ID, EPIC_REDIRECT_URL
from Pisces.decorators import authentication_required
from Pisces import endpoints


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


def logout(request):
    request.session.pop("patient", None)
    request.session.pop("access_token", None)
    request.session.pop("provider", None)
    request.session.pop("endpoint", None)
    return redirect("pisces:home")


def index(request):
    authorization_code = request.GET.get("code")
    if authorization_code and request.session.get("provider"):
        token_json = exchange_token(request.session.get("provider"), authorization_code)
        request.session["access_token"] = token_json.get("access_token")
        request.session["patient"] = token_json.get("patient")
        return redirect("pisces:home")
    providers = endpoints.load_providers()
    return render(request, "index.html", {
        "title": "Pisces by Qiu",
        "providers": providers
    })


def authenticate(request):
    provider = request.GET.get("provider")
    request.session["provider"] = provider
    client_id = EPIC_CLIENT_ID if provider != "Demo" else EPIC_TEST_ID
    authorize_endpoint = endpoints.get_endpoint(provider, "authorize")
    if not authorize_endpoint:
        return HttpResponse("Healthcare provider %s is currently not supported." % provider)
    if provider == "Demo":
        request.session["access_token"] = "X"
        request.session["patient"] = "Tbt3KuCY0B5PSrJvCu2j-PlK.aiHsu2xUjUM8bWpetXoB"
        return redirect("pisces:home")
        
    redirect_url = "%s?response_type=code&client_id=%s&redirect_uri=%s" % (
        authorize_endpoint,
        client_id,
        EPIC_REDIRECT_URL
    )
    return HttpResponseRedirect(redirect_url)


def home(request):
    patient = request.session.get("patient")
    access_token = request.session.get("access_token")
    provider = request.session.get("provider")
    if not (patient and access_token):
        return redirect("pisces:index")
    url = "%s%s/%s" % (endpoints.get_endpoint(provider), "Patient", patient)
    print(url)
    response = requests.get(url, headers=headers(request))
    print(response.content)

    resources = [
        {
            "name": "Laboratory Results",
            "link": "observations"
        }
    ]
    return render(request, "home.html", {
        "title": "Your Data",
        "patient": response.json(),
        "resources": resources,
    })


def headers(request):
    headers = {
        "Accept": "application/json"
    }
    access_token = request.session.get("access_token")
    if access_token and len(access_token) > 10:
        headers["Authorization"] = "Bearer %s" % access_token
    return headers


def observations(request):
    patient = request.session.get("patient")
    access_token = request.session.get("access_token")
    provider = request.session.get("provider")
    if not (patient and access_token):
        return redirect("pisces:index")
    url = "%s%s?patient=%s&category=Laboratory" % (endpoints.get_endpoint(provider), "Observation", patient)
    response = requests.get(url, headers=headers(request))
    print(response.content)

    entries = response.json().get("entry")
    return render(request, "observations.html", {
        "title": "Observations",
        "patient": patient,
        "entries": entries,
        "total": response.json().get("total")
    })
