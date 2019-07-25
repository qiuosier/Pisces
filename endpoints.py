import os
import json
import requests
from lxml import etree
from django.conf import settings


def load_providers():
    with open(os.path.join(settings.BASE_DIR, "Pisces", "EpicEndpoints.json")) as endpoint_json:
        providers = json.load(endpoint_json).get("Entries")
    return providers


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