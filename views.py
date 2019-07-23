import json
import os
import requests
import re
import ast
from lxml import etree
from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from rhythm.private import EPIC_TEST_ID, EPIC_CLIENT_ID, EPIC_REDIRECT_URL


def load_providers():
    with open(os.path.join(settings.BASE_DIR, "Pisces", "EpicEndpoints.json")) as endpoint_json:
        providers = json.load(endpoint_json).get("Entries")
    return providers


def index(request):
    providers = load_providers()
    return render(request, "home.html", {
        "title": "Pisces by Qiu",
        "providers": providers
    })


def get_endpoint(provider, endpoint_name):
    providers = load_providers()
    for entry in providers:
        if entry.get("OrganizationName") == provider:
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
    client_id = EPIC_CLIENT_ID if provider != "Demo" else EPIC_TEST_ID
    authorize_endpoint = get_endpoint(provider, "authorize")
    if not authorize_endpoint:
        return HttpResponse("Healthcare provider %s is currently not supported." % provider)
    redirect_url = "%s?response_type=code&client_id=%s&redirect_uri=%s" % (
        authorize_endpoint,
        client_id,
        EPIC_REDIRECT_URL
    )
    print(redirect_url)
    return HttpResponseRedirect(redirect_url)
