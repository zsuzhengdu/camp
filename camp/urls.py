from django.conf import settings
from django.conf.urls import patterns, include, url
from django.conf.urls.static import static

from django.views.generic.simple import direct_to_template

from django.contrib import admin
admin.autodiscover()

import camp.models

from camp.models import Person
import camp.views

urlpatterns = patterns("",
    url(r"^$", direct_to_template, {"template": "homepage.html"}, name="home"),
    # (r'^(?P<pk>\d)$', camp.views.HybridDetailView.as_view(model=Person)),

    url(r"^tos/$", direct_to_template, {"template": "tos.html"}, name="tos"),
    url(r"^contact/$", direct_to_template, {"template": "contact.html"}, name="contact"),
    url(r"^learn_more/$", direct_to_template, {"template": "learn_more.html"}, name="learn_more"),
    	
	# Multipe types of user redirect
	#url(r"^customer_homepage/$", direct_to_template, {"template": "customer_homepage.html"}, name="customer_home"),
	url(r"^customer_homepage/$", camp.views.CustomerHomeView.as_view(), name="customer_home"),
    url(r"^worker_homepage/$", direct_to_template, {"template": "worker_homepage.html"}, name="worker_home"),
	    
    # Mutiple types of user signup
    url(r"^account/signup/customer/$", camp.views.CustomerSignupView.as_view(), name="customer_account_signup"),
    url(r"^account/signup/worker/$", camp.views.WorkerSignupView.as_view(), name="worker_account_signup"),

    # Unified Login
    url(r"^account/login/$", camp.views.LoginView.as_view(), name="account_login"),
    url(r"^account/logout/$", camp.views.LogoutView, name="account_logout"),
    url(r"^account/", include("account.urls")),    

    
    url(r"^admin/", include(admin.site.urls)),

    # User Actions
    # 1. add a vidoe
    # 2. fund account

    url(r"^customer/add_video/$", camp.views.AddVideoView.as_view(), name="add_video"),    
    #url(r"^customer/fund/$", camp.views.fund, name="fund"),
    url(r"^customer/fund/$", camp.views.FundView.as_view(), name="fund"),
    # Video States
    url(r"^customer/video_info/$", camp.views.CustomerVideoView.as_view(), name="customer_video"),

    url(r"^customer/video_info/(?P<video_id>\d+)/$", camp.views.VideoDetailsView.as_view(), name="video_details"),

    url(r'^notify_url/$', include('paypal.standard.ipn.urls')),

    url(r'^video_list/$', camp.views.VideoListView.as_view(), name='video_list'),    


    # Worker Actions 
    # 1. transcribe and verify video
    # 2. train to level up     
    # 3. apply for QA designation
    
    #url(r"^worker/transcribe/$", camp.views.TranscribeView.as_view(), name="transcribe"),
    url(r"^worker/transcribe/(?P<video_id>\d+)/$", camp.views.TranscribeView.as_view(), name="transcribe"),
    
    url(r"^worker/transcribe_list/$", camp.views.TranscribeListView.as_view(), name="transcribe_list"),

    # url(r"^worker/transcribe/$", direct_to_template, {"template": "transcribe.html"}, name="transcribe"),    
    
    # url(r"^worker/verify/$", camp.views.VerifyView.as_view(), name="verify"),
    url(r"^worker/verify/(?P<video_id>\d+)/$", camp.views.VerifyView.as_view(), name="verify"),

    url(r"^worker/verify_list/$", camp.views.VerifyListView.as_view(), name="verify_list"),


    # url(r"^worker/verify/$", direct_to_template, {"template": "verify.html"}, name="verify"),
    
    url(r"^worker/video_info/$", camp.views.WorkerVideoView.as_view(), name="worker_video"),

    # url(r"^worker/train/$", camp.views.TrainView.as_view(), name="train"),
    url(r"^worker/train/$", direct_to_template, {"template": "train.html"}, name="train"),    
    
    # url(r"^worker/apply_QA/$", camp.views.ApplyQAView.as_view(), name="apply_QA"),
    url(r"^worker/apply_qa/$", direct_to_template, {"template": "apply_qa.html"}, name="apply_qa"),

)

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
