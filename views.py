import json
import os
import traceback
import requests
import re
import ast
import logging
from lxml import etree
from django.conf import settings
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.utils import timezone
from rhythm.private import EPIC_TEST_ID, EPIC_CLIENT_ID, EPIC_REDIRECT_URL
from Pisces.decorators import authentication_required
from Pisces import endpoints, observations
logger = logging.getLogger(__name__)


def exchange_token(provider, authorization_code, redirect_url):
    token_endpoint = endpoints.get_endpoint(provider, "token")
    client_id = EPIC_CLIENT_ID if provider != "Demo" else EPIC_TEST_ID
    data = {
        "grant_type": "authorization_code",
        "code": authorization_code,
        "redirect_uri": redirect_url,
        "client_id": client_id
    }
    response = requests.post(token_endpoint, data, headers=dict(Accept="application/json"))
    logger.debug(response.content)
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
            msg =  "Failed to get patient data.\n Response Code: %s.\n %s" % (
                response.status_code, 
                response.content
            )
            logger.debug(msg)
            request.session["errors"] = msg
            return None
        request.session["patient"] = response.json()
    return request.session.get("patient")


def logout(request):
    request.session.flush()
    return redirect("pisces:home")


def index(request):
    authorization_code = request.GET.get("code")
    provider = request.session.get("provider")
    if "localhost" in request.get_host():
        redirect_uri = "http://" + request.get_host() + "/pisces"
    else:
        redirect_uri = EPIC_REDIRECT_URL
    logger.debug("Provider: %s, Authorization Code: %s" % (provider, authorization_code))
    if authorization_code and provider:
        logger.debug("Provider: %s, Authorization Code: %s" % (provider, authorization_code))
        token_json = exchange_token(provider, authorization_code, redirect_uri)
        logger.debug(token_json)
        return initialize_session(request, token_json.get("access_token"), token_json.get("patient"))
    access_token = request.GET.get("access_token")
    patient_id = request.GET.get("patient_id")
    if access_token and patient_id and provider:
        logger.debug("Access code and patient ID found in GET request.")
        return initialize_session(request, access_token, patient_id)
    providers = endpoints.load_providers()
    # Index page displays and clear the errors.
    errors = request.session.pop("errors", None)
    return render(request, "index.html", {
        "title": "Pisces",
        "providers": providers,
        "top_providers": ["Demo", "Duke Health"],
        "errors": errors,
    })

def initialize_session(request, access_token, patient_id):
    request.session["access_token"] = access_token
    request.session["patient_id"] = patient_id
    request.session["patient"] = get_patient_info(request)
    request.session["expiration"] = timezone.now() + timezone.timedelta(seconds=3500)
    if request.session["access_token"] and request.session["patient_id"]:
        return redirect("pisces:home")
    return HttpResponse("Authentication Failed.")

def authenticate(request):
    provider = request.GET.get("provider")
    request.session["provider"] = provider
    client_id = EPIC_CLIENT_ID if provider != "Demo" else EPIC_TEST_ID
    if provider == "Demo":
        logger.debug("Connecting to sandbox...")
        request.session["access_token"] = "X"
        request.session["patient_id"] = "Tbt3KuCY0B5PSrJvCu2j-PlK.aiHsu2xUjUM8bWpetXoB"
        request.session["patient"] = get_patient_info(request)
        request.session["expiration"] = timezone.now() + timezone.timedelta(seconds=3500)
        return redirect("pisces:home")
    if "localhost" in request.get_host():
        redirect_uri = "http://" + request.get_host() + "/pisces"
    else:
        redirect_uri = EPIC_REDIRECT_URL
    try:
        authenticate_url = endpoints.get_authentication_url(
            client_id=client_id,
            provider=provider,
            redirect_uri=redirect_uri
        )
    except NotImplementedError as ex:
        return HttpResponse(ex.args)
    logger.debug("Redirect URL: %s" % authenticate_url)
    return HttpResponseRedirect(authenticate_url)


@authentication_required
def home(request):
    patient = get_patient_info(request)
    resources = [
        {
            "name": "Laboratory Results",
            "link": "observations/Laboratory"
        }
    ]
    return render(request, "home.html", {
        "title": "Your Data",
        "patient": patient,
        "resources": resources,
    })


@authentication_required
def view_observations(request, category):
    observation_class = getattr(observations, category)
    if not observation_class:
        return HttpResponseBadRequest("%s is not supported." % category)
    patient_id = request.session.get("patient_id")
    api = endpoints.initialize_api(request)
    response = api.get("Observation", patient=patient_id, category=category)
    entries = None
    try:
        data = response.json()
        entries = data.get("entry")
    except:
        traceback.print_exc()
    if not entries:
        return HttpResponse("Failed to obtain %s data." % category)
    groups = observation_class(entries).group_by_code()
    return render(request, "observations.html", {
        "title": "Observations",
        "data": data,
        "groups": groups,
        "total": len(groups.keys())
    })


@authentication_required
def view_laboratory(request, code):
    patient_id = request.session.get("patient_id")
    api = endpoints.initialize_api(request)
    response = api.get("Observation", patient=patient_id, category="Laboratory")
    entries = None
    try:
        data = response.json()
        entries = data.get("entry")
    except:
        pass
    if not entries:
        return HttpResponse("Failed to obtain Laboratory data.")
    groups = observations.Laboratory(entries).group_by_code()
    resources = groups.get(code)
    if resources:
        title = resources[0].get("code", dict()).get("text")
    else:
        title = "N/A"
    return render(request, "results.html", {
        "title": title,
        "data": data,
        "resources": resources,
    })
