# store/test_urls.py - Temporary test file
from django.http import HttpResponse

def test_view(request):
    print("🎯 TEST VIEW IS WORKING!")
    return HttpResponse("TEST VIEW WORKS!")

def test_track_order(request):
    print("🎯 TEST TRACK ORDER IS WORKING!")
    return HttpResponse("TEST TRACK ORDER WORKS!")