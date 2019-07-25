import os
import json
import requests
from lxml import etree
from django.conf import settings
from Aries.web import WebAPI


def load_providers():
    with open(os.path.join(settings.BASE_DIR, "Pisces", "EpicEndpoints.json")) as endpoint_json:
        providers = json.load(endpoint_json).get("Entries")
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


def initialize_api(request):
    provider = request.session.get("provider")
    access_token = request.session.get("access_token")
    web_api = WebAPI(get_endpoint(provider))
    web_api.add_header(
        Accept="application/json",
        Authorization="Bearer %s" % access_token
    )
    return web_api
