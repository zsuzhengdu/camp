# Write Fucking view class 
from django.core.mail import send_mail
from django.shortcuts import redirect, get_object_or_404, render_to_response
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseServerError
from django.core.urlresolvers import reverse
from django.core import serializers
from django.template import RequestContext
from django.contrib.auth.models import User
from django.views.generic.edit import FormView, View
from django.views.generic import ListView, TemplateView

from account.utils import default_redirect, user_display

from camp.forms import *
import camp.views
import camp.models
import account.views
import settings
import urlparse 

from account.models import Account
from account.utils import default_redirect, user_display
from camp.models import Customer, Worker, Video


class CustomerSignupView(account.views.SignupView):


    THEME_ACCOUNT_CONTACT_EMAIL = "zsuzhengdu@gmail.com"
    template_name = "customer_signup.html"
   #  template_name_ajax = "customer_signup.html"

    def get(self, *args, **kwargs):
        if self.request.user.is_authenticated():
            return redirect(default_redirect(self.request, settings.CUSTOMER_ACCOUNT_LOGIN_REDIRECT_URL))
        if not self.is_open():
            return self.closed()
        return super(CustomerSignupView, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        if not self.is_open():
            return self.closed()
        return super(CustomerSignupView, self).post(*args, **kwargs)
    
    def get_success_url(self, fallback_url=None, **kwargs):
        if fallback_url is None:
            #fallback_url = settings.CUSTOMER_ACCOUNT_SIGNUP_REDIRECT_URL
            fallback_url = settings.ACCOUNT_SIGNUP_REDIRECT_URL
        kwargs.setdefault("redirect_field_name", self.get_redirect_field_name())
        return default_redirect(self.request, fallback_url, **kwargs)

    def after_signup(self, form):

        self.create_profile(form)
        super(CustomerSignupView, self).after_signup(form)    

    def create_profile(self, form):
        
        profile = self.created_user.get_profile()   # type(profile) == Account.models.account
        profile.save()

        customer = Customer()
        customer.account = profile
        customer.save()

    def email_confirmation_required_response(self):
        if self.request.is_ajax():
            template_name = self.template_name_email_confirmation_sent_ajax
        else:
            template_name = self.template_name_email_confirmation_sent
        response_kwargs = {
            "request": self.request,
            "template": template_name,
            "context": {
                "email": self.created_user.email,
                "success_url": self.get_success_url(),
                "THEME_ACCOUNT_CONTACT_EMAIL": "info@HiveScribe.com"
            }
        }
        return self.response_class(**response_kwargs)


class WorkerSignupView(account.views.SignupView):
      
    template_name = "worker_signup.html"
    template_name_ajax = "worker_signup.html"

    def get(self, *args, **kwargs):
        if self.request.user.is_authenticated():
            return redirect(default_redirect(self.request, settings.WORKER_ACCOUNT_LOGIN_REDIRECT_URL))
        if not self.is_open():
            return self.closed()
        return super(WorkerSignupView, self).get(*args, **kwargs)

    def get_success_url(self, fallback_url=None, **kwargs):
        if fallback_url is None:
            fallback_url = settings.ACCOUNT_SIGNUP_REDIRECT_URL
        kwargs.setdefault("redirect_field_name", self.get_redirect_field_name())
        return default_redirect(self.request, fallback_url, **kwargs)

    def after_signup(self, form):
        self.create_profile(form)
        super(WorkerSignupView, self).after_signup(form)

    def create_profile(self, form):        
        profile = self.created_user.get_profile()   # type(profile) == Account.models.account
        profile.save()

        worker = Worker()
        worker.account = profile
        worker.save()

    def email_confirmation_required_response(self):
        if self.request.is_ajax():
            template_name = self.template_name_email_confirmation_sent_ajax
        else:
            template_name = self.template_name_email_confirmation_sent
        response_kwargs = {
            "request": self.request,
            "template": template_name,
            "context": {
                "email": self.created_user.email,
                "success_url": self.get_success_url(),
                "THEME_ACCOUNT_CONTACT_EMAIL": "info@HiveScribe.com"
            }
        }
        return self.response_class(**response_kwargs)


# Unified Login View
class LoginView(account.views.LoginView):

    def get_success_url(self, fallback_url=None, **kwargs):
        customer = Customer.objects.filter(account = self.request.user.get_profile())

        if fallback_url is None:
            if customer:
                fallback_url = settings.CUSTOMER_ACCOUNT_LOGIN_REDIRECT_URL
            else:
                fallback_url = settings.WORKER_ACCOUNT_LOGIN_REDIRECT_URL
        kwargs.setdefault("redirect_field_name", self.get_redirect_field_name())
        return default_redirect(self.request, fallback_url, **kwargs)



class ConfirmEmailView(account.views.ConfirmEmailView):

    def get_redirect_url(self):
        if self.request.user.is_authenticated():
            customer = Customer.objects.filter(account = self.request.user.get_profile())
            if customer:
                return settings.CUSTOMER_EMIAL_CONFIRMATION_REDIRECT_URL
            else:   # if it is worker
                return settings.WORKER_EMIAL_CONFIRMATION_REDIRECT_URL 
        else:
            return settings.ACCOUNT_EMAIL_CONFIRMATION_ANONYMOUS_REDIRECT_URL

from django.contrib import auth
from django.contrib.auth import authenticate, login, logout
def LogoutView(request):
    auth.logout(request)
    return redirect('home')

# Dashboard View for Customer
class CustomerHomeView(View):


    def get(self, *args, **kwargs):
        print '----> Customer homepage'    
        print self.request.user
        
        customer = Customer.objects.get(account = self.request.user.get_profile())
        # customer.fund = '0'
        video_done = 0
        for video in customer.videos.all():
            if video.videostate == 'done':
                video_done = video_done + 1
                
        video_wip = customer.videos.count() - video_done
        
        return render_to_response('customer_homepage.html', {"customer": customer, 'video_done': video_done, "video_wip": video_wip, "request": self.request, "SITE_NAME": 'HiveScribe'})
        

#Boto S3 API libraries to talk to the S3
import boto
from boto.s3.key import Key
import os

# Django Signal Solution
"""
from django.dispatch import Signal
upload = Signal(providing_args = ['path'])

def s3_upload(**kwargs):

    path = kwargs['path']

    bucket_name = settings.BUCKET_NAME
    conn = boto.connect_s3(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
    bucket = conn.get_bucket(bucket_name)  
    k = Key(bucket)
    k.key = path     # set the key value using path + filename you would store your file (e.g. video_path + video_file_name)
                     # key is the path you store the file on amazon s3  

    fp = open(path)  # exception test
    # set conttents from local drive to S3, which gives bad user experience in sysc mode. Try to write in async mode. (Subprocess or Celery)
    k.set_contents_from_file(fp)        
    fp.close()
             
    # we need to make it public so it can be accessed publicly
    # using a URL like http://s3.amazonaws.com/bucket_name/key
    k.make_public()

    os.remove(path)

upload.connect(s3_upload)
"""


# Django Multiple Process Solution
import multiprocessing
from multiprocessing import Process

####
    # Must find a better way for uploading video to s3, local cache or S3 upload APP
####

def s3_upload(request, path):

    bucket_name = settings.BUCKET_NAME
    conn = boto.connect_s3(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
    bucket = conn.get_bucket(bucket_name)  
    k = Key(bucket)
    k.key = path     # set the key value using path + filename you would store your file (e.g. video_path + video_file_name)
                     # key is the path you store the file on amazon s3  

    fp = open(path)  # exception test
    # set conttents from local drive to S3, which gives bad user experience in sysc mode. Try to write in async mode. (Subprocess or Celery)
    k.set_contents_from_file(fp)        
    fp.close()
             
    # we need to make it public so it can be accessed publicly
    # using a URL like http://s3.amazonaws.com/bucket_name/key
    k.make_public()

    os.remove(path)


class AddVideoView(FormView):

    template_name = 'add_video.html'
    form_class = VideoForm
    success_url = '/customer_homepage/'      

    def form_valid(self, form):
        print '---> form_valid'
        video = self.create_video(form)
        self.update_videoowner(video)

        if video.videopath:
            print 'video path on local'
            path = settings.MEDIA_ROOT + '/' + str(video.videopath)
            print path

            video.videopath = "http://s3.amazonaws.com/campcode" + path
            video.save()
            
            #self.s3_upload(path)       # Inner Class Method
            
            # upload.send(sender="upload", path = path)         # Django Signal
            
            p = multiprocessing.Process(target=s3_upload, args=(self.request, path))
            p.start()



        #self.after_upload()
        return super(AddVideoView, self).form_valid(form)

    def create_video(self, form, **kwargs):
        print 'Data grabed from front end'
        video = Video(
            videoname = form.cleaned_data.get("videoname"),
            videopath = form.cleaned_data.get("path"),
            videourl = self.parse_url(form.cleaned_data.get("url")),           
            # Update state of video
            videostate = "uploaded"    
        )
        video.save()
        return video
   
    def parse_url(self, url):
        if not url:
            return url
        url_data = urlparse.urlparse(url)
        query = urlparse.parse_qs(url_data.query)
        return "https://www.youtube.com/v/" + query["v"][0] + "?version=3"
     
    def update_videoowner(self, video):
        print '----> videoowner_update'
        customer = Customer.objects.get(account = self.request.user.get_profile())
        customer.videos.add(video)
        customer.save() 

        print '*' * 10
        print 'onwer of video'
        print customer
        print '*' * 10  

    """    
    def s3_upload(self, path):

        bucket_name = settings.BUCKET_NAME
        conn = boto.connect_s3(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
        bucket = conn.get_bucket(bucket_name)  
        k = Key(bucket)
        k.key = path     # set the key value using path + filename you would store your file (e.g. video_path + video_file_name)
                         # key is the path you store the file on amazon s3  

        fp = open(path)  # exception test
        # set conttents from local drive to S3, which gives bad user experience in sysc mode. Try to write in async mode. (Subprocess or Celery)
        k.set_contents_from_file(fp)        
        fp.close()
             
        # we need to make it public so it can be accessed publicly
        # using a URL like http://s3.amazonaws.com/bucket_name/key
        k.make_public()

        os.remove(path)
    """

                
    # Broadcast video transcribing request to qualified transcriber (worker)    
    # Note: Check the existence of qualified worker
    # Rewrite by using Django Signals in future
    def after_upload(self, **kwargs):
        
        subject = "Here comes jobs!"
        message = "Look, transcribing jobs!!!"
        # Broadcast newly uploaded video info to 'qualified' workers, e.g, worker.level >= '10'
        for worker in Worker.objects.all():
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [worker.account.user.email])         

class VideoDetailsView(TemplateView):
    template_name = 'video.html'

    def get_context_data(self, **kwargs):
        context = super(VideoDetailsView, self).get_context_data(**kwargs)
        context['video'] = Video.objects.get(pk=self.kwargs.get('video_id', None))
        return context


class VideoListView(ListView):
    template_name = 'video_list.html'
    paginate_by = 5
    context_object_name = 'videos'
    model = Video

    def get_queryset(self):
        return Customer.objects.get(account = self.request.user.get_profile()).videos.all()


class CustomerVideoView(View):
    
    def get(self, *args, **kwargs):

        print '----> CustomerVideoView'
        print 'self.request'
        print self.request

        customer = Customer.objects.get(account = self.request.user.get_profile())
        video_in_completed = self.video_completed(customer)
        video_in_process = self.video_process(customer)

        return render_to_response('customer_video.html', 
                                    {"customer": customer, "request": self.request, "SITE_NAME": 'HiveScribe', "video_in_completed": video_in_completed, "video_in_process": video_in_process}
                                 )

    def video_completed(self, customer):
        return [video for video in customer.videos.all() if 'completed' == video.videostate]

    def video_uploaded(self, customer):
        return [video for video in customer.videos.all() if 'uploaded' == video.videostate]

    def video_process(self, customer):
        return [video for video in customer.videos.all() if 'completed' != video.videostate]
            

class PlayerView(View):
    pass


class WorkerVideoView(View):
    def get(self, *args, **kwargs):
        #print self.request.user
        worker = Worker.objects.get(account = self.request.user.get_profile())
        # customer.fund = '0'
        return render_to_response('worker_video.html', {"worker": worker, "request": self.request, "SITE_NAME": 'HiveScribe'})

class FundView(FormView):
    #print '----> FundView'

    template_name = 'fund.html'
    form_class = FundForm


    def get(self, *args, **kwargs):
        return super(FundView, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        return super(FundView, self).post(*args, **kwargs) 

    def form_valid(self, form):
        print '----> form_valid'        
        return super(FundView, self).form_valid(form)
        
    def get_success_url(self, fallback_url=None, **kwargs):
        # Redirect to previous url
        if fallback_url is None:
            fallback_url = paypal_url
        return default_redirect(self.request, fallback_url, **kwargs)

    # update customer instance when customer's payment is verified    
    def update_customer(self, form):
        print '----> update_customer'
        customer = Customer.objects.get(account = self.request.user.get_profile())
        fund = float(form.cleaned_data.get("fund"))

        if customer.fund == '':
            customer.fund = str(fund) 
        else:
            customer.fund = str(float(customer.fund) + fund)
        
        customer.save()

    def after_fund(self, **kwargs):
        print '----> after_fund'
        pass

####
    # View for Worker
####


####
    # Ajax Test
####

import json

from django.http import HttpResponse
from django.views.generic.edit import CreateView


class AjaxableResponseMixin(object):
    """
    Mixin to add AJAX support to a form.
    Must be used with an object-based FormView (e.g. CreateView)
    """
    def render_to_json_response(self, context, **response_kwargs):
        data = json.dumps(context)
        response_kwargs['content_type'] = 'application/json'
        return HttpResponse(data, **response_kwargs)

    def form_invalid(self, form):
        response = super(AjaxableResponseMixin, self).form_invalid(form)
        if self.request.is_ajax():

            print 'ajax request'

            return self.render_to_json_response(form.errors, status=400)
        else:
            print 'regular request'

            return response
            
    def form_valid(self, form):
        # We make sure to call the parent's form_valid() method because
        # it might do some processing (in the case of CreateView, it will
        # call form.save() for example).
        response = super(AjaxableResponseMixin, self).form_valid(form)
        if self.request.is_ajax():
            data = {
                #'pk': self.object.pk,
                'pk': '1',
            }

            print 'ajax request'

            return self.render_to_json_response(data)
        else:

            print 'regular request'

            return response

    
class TranscribeView(FormView):

    # print '----> TranscribeView'

    template_name = 'transcribe.html'
    form_class = TranscribtionForm
    success_url = '/worker_homepage/'

    def get(self, *args, **kwargs):
        if self.request.user.is_authenticated():
            form_class = self.get_form_class()
            form = self.get_form(form_class)
            video = Video.objects.get(pk=self.kwargs.get('video_id', None))
            # 
            # someone checked video out and is editing video
            #

            video.videostate = 'WIP'
            video.save()

            worker = Worker.objects.get(account = self.request.user.get_profile())
            
            worker.videos.add(video)
            worker.save()

            print '*' * 10
            print str(self.request.user) + ' is transcribing the video ---- State of Video is WIP'
            print '*' * 10

            form = TranscribtionForm({'transcribtion': video.transcribtion})
            ctx = self.get_context_data(form=form)

            return self.render_to_response(ctx)
    
    def form_valid(self, form):
        # We make sure to call the parent's form_valid() method because
        # it might do some processing (in the case of CreateView, it will
        # call form.save() for example).
        response = super(TranscribeView, self).form_valid(form)

        form_class = self.get_form_class()
        form = self.get_form(form_class)
        ctx = self.get_context_data(form=form)

        if self.request.is_ajax():
            data = {}
            video = Video.objects.get(pk=self.kwargs.get('video_id', None))
            video.transcribtion = self.request.POST['transcribtion'] 
            video.save()

            """
            print 'posted data'
            print self.request.POST['transcribtion']   
            print 'auto saved video transcribtion'
            print video.transcribtion 
            print 'ajax request'
            """

            print 'transcribtion automatically saved'

            return self.render_to_json_response(data)

        else:
            """
            print 'regular request'
            """

            video = Video.objects.get(pk=self.kwargs.get('video_id', None))
            video.transcribtion = self.request.POST['transcribtion'] 
            #
            # Done (Transcriber submitted the form)
            #
            video.videostate = "done"
            video.save()

            print '*' * 10
            print 'The state of vidoe is Done'
            print '*' * 10

            return response


    """        
    def form_valid(self, form):
        print '----> form_valid'
        #self.add_transcrition(form)
        return super(TranscribeView, self).form_valid(form)
    """    
    def render_to_json_response(self, context, **response_kwargs):
        data = json.dumps(context)
        response_kwargs['content_type'] = 'application/json'
        return HttpResponse(data, **response_kwargs)

    def get_context_data(self, **kwargs):
        context = super(TranscribeView, self).get_context_data(**kwargs)
        context['video'] = Video.objects.get(pk=self.kwargs.get('video_id', None))
        return context

    def add_transribtion(self, form, **kwargs):
        print 'add_transribtion'
        pass
        # video = Video.objection.get(videoname = self.request.videoname)
        # video.transcribtion = form.cleaned_data.get("transcribtion")    

    def after_transcribe(self, **kwargs):
        # Notify all qualified QA
        subject = "Here comes jobs!"
        message = "Look, verificatino jobs!!!"
        # Broadcast newly uploaded video info to 'qualified' workers, e.g, worker.level >= '10'
        for worker in Worker.objects.all():
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [worker.account.user.email])         

class TranscribeListView(ListView):
    template_name = 'transcribe_list.html'
    paginate_by = 5
    context_object_name = 'videos'
    model = Video
     

    def get_queryset(self):
        # return Video.objects.all()

        print 'get get_queryset'
        print Video.objects.all()
        print type(Video.objects.all())
        print Video.objects.filter(videostate = 'WIP')

        return Worker.objects.get(account = self.request.user.get_profile()).videos.all() | Video.objects.filter(videostate = 'uploaded')

class VerifyView(FormView):

    # print '----> VerifyView'
    template_name = 'verify.html'
    form_class = VerificationForm
    success_url = '/worker_homepage/'


    def get(self, *args, **kwargs):
        if self.request.user.is_authenticated():
            form_class = self.get_form_class()
            form = self.get_form(form_class)
            ctx = self.get_context_data(form=form)
            return self.render_to_response(ctx)

    def get_context_data(self, **kwargs):
        context = super(VerifyView, self).get_context_data(**kwargs)
        context['video'] = Video.objects.get(pk=self.kwargs.get('video_id', None))
        return context

    def form_valid(self, form):
        print '----> form_valid'
        self.add_verification(form)
        return super(VerifyView, self).form_valid(form)

    def add_verification(self, form, **kwargs):
        print '----> add_verification'
        pass
        # video = Video.objection.get(videoname = self.request.videoname)
        # video.verification = form.cleaned_data.get("verification")    

    def after_verify(self, **kwargs):
        print '----> after_verify'
        # Nofity our QAs/Manager to make 'randomly' double check
        pass


class VerifyListView(ListView):
    template_name = 'verify_list.html'
    paginate_by = 3
    context_object_name = 'videos'
    model = Video

    def get_queryset(self):
        return Video.objects.all()


class TrainView(FormView):
    def after_train(self, **kwargs):
        pass

class ApplyQAView(FormView):
    def after_applyQA(self, **kwargs):
        pass    


from django.http import HttpResponse
from django.utils import simplejson
from django.views.generic.detail import BaseDetailView, SingleObjectTemplateResponseMixin

class JSONResponseMixin(object):
    def render_to_response(self, context):
        return self.get_json_response(self.convert_context_to_json(context))
    def get_json_response(self, content, **httpresponse_kwargs):
        return HttpResponse(content, content_type='application/json', **httpresponse_kwargs)
    def convert_context_to_json(self, context):
        return simplejson.dumps(context)

class HybridDetailView(JSONResponseMixin, SingleObjectTemplateResponseMixin, BaseDetailView):
    
    template_name = 'person_detail.html'

    def render_to_response(self, context):
        if self.request.is_ajax():
            obj = context['object'].as_dict()
            return JSONResponseMixin.render_to_response(self, obj)
        else:
            return SingleObjectTemplateResponseMixin.render_to_response(self, context)
