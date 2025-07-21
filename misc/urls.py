from django.urls import path

from . import views

app_name='misc'

urlpatterns = [
    path('search/', views.search, name='search'),
    path('terms/', views.terms, name='terms'),
    path('auth/', views.authenticated, name='auth'),
    path('time/', views.time, name='time'),
    path('ad/', views.ad, name='ad'),
    path('ads.txt', views.adstxt, name='adstxt'),
    path('robots.txt', views.robotstxt, name='robotstxt'),
    path('idscan/', views.idscan, name='idscan'),
    path('sitemap.xml', views.sitemap, name='sitemap'),
    path('news.xml', views.news, name='news'),
    path('map/', views.map, name='map'),
    path('upload/', views.upload_video_api, name='upload'),
    path('site.webmanifest', views.webmanifest, name='webmanifest'),
    path('serviceworker.js', views.service_worker, name='serviceworker'),
]
