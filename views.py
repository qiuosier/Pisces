import json
import os
import requests
import re
import ast
from lxml import etree
from django.conf import settings
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from rhythm.private import EPIC_TEST_ID, EPIC_CLIENT_ID, EPIC_REDIRECT_URL


def load_providers():
    with open(os.path.join(settings.BASE_DIR, "Pisces", "EpicEndpoints.json")) as endpoint_json:
        providers = json.load(endpoint_json).get("Entries")
    return providers


def index(request):
    authorization_code = request.GET.get("code")
    if authorization_code and request.session.get("provider"):
        token_json = exchange_token(request.session.get("provider"), authorization_code)
        request.session["access_token"] = token_json.get("access_token")
        request.session["patient"] = token_json.get("patient")
        return redirect("pisces:home")
    providers = load_providers()
    return render(request, "index.html", {
        "title": "Pisces by Qiu",
        "providers": providers
    })


def exchange_token(provider, authorization_code):
    token_endpoint = get_endpoint(provider, "token")
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


def get_endpoint(provider, endpoint_name=None):
    providers = load_providers()
    for entry in providers:
        if entry.get("OrganizationName") == provider:
            if not endpoint_name:
                return entry.get("FHIRPatientFacingURI")
            if entry.get(endpoint_name):
                return entry.get(endpoint_name)
            else:
                meta_url = entry.get("FHIRPatientFacingURI")
                if meta_url:
                    return request_endpoint(meta_url + "metadata", endpoint_name)
    return None


def request_endpoint(meta_url, endpoint_name):
    print(meta_url)
    response = requests.get(meta_url)
    content = response.content
    content_type = response.headers['Content-Type']
    if "xml" in content_type:
        root = etree.fromstring(response.content)
        extensions = root.findall(".//extension/extension", root.nsmap)
        for extension in extensions:
            if extension.get("url") == endpoint_name:
                node = extension.find(".//valueUri", root.nsmap)
                if node is not None:
                    return node.get("value")
    return None


def authenticate(request):
    provider = request.GET.get("provider")
    request.session["provider"] = provider
    client_id = EPIC_CLIENT_ID if provider != "Demo" else EPIC_TEST_ID
    authorize_endpoint = get_endpoint(provider, "authorize")
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
    url = "%s%s/%s" % (get_endpoint(provider), "Patient", patient)
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
    url = "%s%s?patient=%s&category=Laboratory" % (get_endpoint(provider), "Observation", patient)
    response = requests.get(url, headers=headers(request))
    print(response.content)

    entries = response.json().get("entry")
    return render(request, "observations.html", {
        "title": "Observations",
        "patient": patient,
        "entries": entries,
        "total": response.json().get("total")
    })
