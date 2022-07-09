import os
import json
import requests
from lxml import etree
from django.conf import settings
from Aries.web import WebAPI


ENDPOINT_BUNDLE_URL = "https://open.epic.com/Endpoints/DSTU2"


def load_providers():
    """Load a list of provider names and endpoints from Epic.
    """
    response = requests.get(ENDPOINT_BUNDLE_URL).json()
    providers = [
        entry["resource"]
        for entry in response["entry"]
        if entry["resource"]["resourceType"] == "Endpoint"
    ]
    providers.append({
        "resourceType": "Endpoint",
        "name": "Demo",
        "address": "https://open-ic.epic.com/FHIR/api/FHIR/DSTU2/"
    })
    providers.sort(key=lambda x: x["name"])
    return providers


PROVIDERS = load_providers()


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


def get_endpoint(provider, endpoint_name=None):
    for entry in PROVIDERS:
        if entry.get("name") == provider:
            if not endpoint_name:
                return entry.get("address")
            if entry.get(endpoint_name):
                return entry.get(endpoint_name)
            else:
                meta_url = entry.get("address")
                if meta_url:
                    return request_endpoint(meta_url + "metadata", endpoint_name)
    return None


def get_authentication_url(client_id, provider, redirect_uri):
    authorize_endpoint = get_endpoint(provider, "authorize")

    aud = None
    for entry in PROVIDERS:
        if entry.get("name") == provider:
            aud = entry["address"]

    if not authorize_endpoint or not aud:
        raise NotImplementedError("Healthcare provider %s is currently not supported." % provider)

    return "%s?response_type=code&client_id=%s&redirect_uri=%s&aud=%s" % (
        authorize_endpoint,
        client_id,
        redirect_uri,
        aud
    )


def initialize_api(request):
    provider = request.session.get("provider")
    access_token = request.session.get("access_token")
    web_api = WebAPI(get_endpoint(provider))
    web_api.add_header(
        Accept="application/json",
        Authorization="Bearer %s" % access_token
    )
    return web_api
