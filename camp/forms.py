import re
import os
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import NON_FIELD_ERRORS
from django.forms.fields import DateField, ChoiceField, MultipleChoiceField
from django.forms.widgets import RadioSelect, CheckboxSelectMultiple, Select
from django.forms.extras.widgets import SelectDateWidget

from paypal.standard.conf import *
from paypal.standard.widgets import ValueHiddenInput, ReservedValueHiddenInput
from paypal.standard.conf import (POSTBACK_ENDPOINT, SANDBOX_POSTBACK_ENDPOINT, 
    RECEIVER_EMAIL)

import account.forms
from camp.models import Video
import settings

from django.template.defaultfilters import filesizeformat

alnum_re = re.compile(r'^\w+$')
youtube_url_re = re.compile(r'(https?://)?(www\.)?youtube\.(com|nl)/watch\?v=([-\w]+)')	

class CustomerSignupForm(account.forms.SignupForm):
	# Add new fields as needed 
	pass

class WorkerSignupForm(account.forms.SignupForm):
	# Add new fields as needed
	pass	

class VideoForm(forms.Form):

	videoname = forms.CharField(
		label = "Vidoe name",
		max_length = 30,
		required = True, 
	)

	VIDEO_SOURCE = ((1, 'Local Drive'), (2, 'YouTube'))
	
	videosource = forms.ChoiceField(
		label = "Video source",
		widget=forms.Select, 
		choices=VIDEO_SOURCE
	)

	
	path = forms.FileField(
		label = "File Path for Video",
		required = False
	)

	def clean_path(self):

		content = self.cleaned_data['path']
		if not content:
			return
		if content.content_type in settings.CONTENT_TYPES:
			if content._size > settings.MAX_UPLOAD_SIZE:
				raise forms.ValidationError(_('The uploaded file size is bigger than 50 MB'))
		else:
			raise forms.ValidationError(_('Please upload a video file with exention .flv, .mov or .mp4'))
		return content	

	#path = ExtFileField(ext_whitelist=(".flv", ".mov", "mp4"), label="File path for video", required=True)

	url = forms.CharField(
		label = "YouTube Video url",
		#validators=[validate_url],
		required = False
	)


	def clean_url(self):
		if not self.cleaned_data.get('url'):
			return self.cleaned_data.get('url')
		elif not youtube_url_re.search(self.cleaned_data.get('url')):
			raise forms.ValidationError(_("Please input a valid YouTube URL."))	
		return self.cleaned_data.get('url')

	
	bid = forms.FloatField(
		label = "Bid",
		max_value=1000,
		min_value=15,
		required=True
	)
	

	"""	
	VIDEO_AREA = (('0', '-------'), ('1', 'Technology'), ('2', 'Science'))

	area = forms.ChoiceField(
		label = 'Fields of video',
		widget=forms.Select,
		choices=VIDEO_AREA,
		required=True
	)

	def clean_area(self):
		data = self.cleaned_data.get('area')

		if data == self.fields['area'].choices[0][0]:
			raise forms.ValidationError('This field is required')
		return data

	TRANSCRIPTION_TYPE = (('0', '-------'), ('1', "Content Oriented"), ('2', "Verbatim"))

	transcribtion_type = forms.ChoiceField(
		label="Transcribtion type",
		widget=forms.Select,
		choices = TRANSCRIPTION_TYPE,
		required=True
	)

	def clean_transcribtion_type(self):
		data = self.cleaned_data.get('transcribtion_type')

		if data == self.fields['transcribtion_type'].choices[0][0]:
			raise forms.ValidationError('This field is required')
		return data

	VIDEO_LANGUAGE = (('0', '-------'), ('1', 'English'), ('2', 'French'))

	language = forms.ChoiceField(
		label= "Language",
		widget=forms.Select,
		choices=VIDEO_LANGUAGE,
		required=True
	)

	def clean_language(self):
		data = self.cleaned_data.get('language')

		if data == self.fields['language'].choices[0][0]:
			raise forms.ValidationError('This field is required')
		return data

		
	bid = forms.IntegerField(
		label = "How much are you willing to pay",
		widget=forms.HiddenInput(),
		max_value = 1000,
		min_value = 0,
		required = False
	)
	
	note = forms.CharField(
		initial="Leave some notes...", 
		widget=forms.Textarea, 
		required=False
	)
	"""
	
	notify = forms.BooleanField(
		label = "Notify me when video is transcribed",
		required = False,
	)
	
	
	def clean_videoname(self):

		if not alnum_re.search(self.cleaned_data["videoname"]):
			raise forms.ValidationError(_("Videonames can only contain letters, numbers and underscores."))
		qs = Video.objects.filter(videoname = self.cleaned_data["videoname"])

		# Unique check of video
		if not qs.exists():
			return self.cleaned_data["videoname"]

		raise forms.ValidationError(_("This videoname is already taken. Please choose another."))
		

	def clean(self):

		if "path" in self.cleaned_data and "url" in self.cleaned_data:
			if not self.cleaned_data['path'] and not self.cleaned_data['url']:
				# print 'path and url are empty'
				raise forms.ValidationError("You must at least choose a file or provide a video link")

		return self.cleaned_data


class TranscribtionForm(forms.Form):
	
	transcribtion = forms.CharField(

		label="Please transcribe the video...", 
		widget=forms.Textarea, 
		required=True
	)




class VerificationForm(forms.Form):
	
	verification = forms.CharField(
		label=" Please verify the transcribtion of the video", 
		widget=forms.Textarea, 
		required=True
	)


from paypal.standard.forms import PayPalPaymentsForm

class AmountForm(forms.Form):
	fund = forms.FloatField(
		max_value=1000,
		min_value=10,
		required=True
	)


class FakeForm(forms.Form):
	pass
	#fake = forms.CharField(widget=forms.HiddenInput(), initial="fale_field")

CMD_CHOICES = (
	("_xclick", "Buy now or Donations"), 
    ("_cart", "Shopping cart"), 
    ("_xclick-subscriptions", "Subscribe")
)

SHIPPING_CHOICES = ((1, "No shipping"), (0, "Shipping"))

NO_NOTE_CHOICES = ((1, "No Note"), (0, "Include Note"))

RECURRING_PAYMENT_CHOICES = (
    (1, "Subscription Payments Recur"), 
	(0, "Subscription payments do not recur")
)

REATTEMPT_ON_FAIL_CHOICES = (
	(1, "reattempt billing on Failure"), 
    (0, "Do Not reattempt on failure")
)

class FundForm(forms.Form):

	fund = forms.FloatField(
		max_value=1000,
		min_value=10,
		initial=15,
		required=True
	)

	business = forms.CharField(widget=ValueHiddenInput(), initial=settings.PAYPAL_RECEIVER_EMAIL)
	amount = forms.IntegerField(widget=ValueHiddenInput(), initial=0)
	item_name = forms.CharField(widget=ValueHiddenInput(), initial="HiveScribe Close Captioning Service Topup")

	# IPN control
	notify_url = forms.CharField(widget=ValueHiddenInput(), initial=settings.PAYPAL_NOTIFY_URL)
	cancel_return = forms.CharField(widget=ValueHiddenInput(), initial=settings.PAYPAL_CANCEL_URL)
	return_url = forms.CharField(widget=ReservedValueHiddenInput(attrs={"name":"return"}), initial=settings.PAYPAL_RETURN_URL, required=False)

	# Default fields
	cmd = forms.CharField(widget=forms.HiddenInput(), initial="_xclick", required=False)
	charset = forms.CharField(widget=forms.HiddenInput(), initial="utf-8")
	currency_code = forms.CharField(widget=forms.HiddenInput(), initial="CAD")
	no_shipping = forms.ChoiceField(widget=forms.HiddenInput(), choices=SHIPPING_CHOICES, initial=SHIPPING_CHOICES[0][0])








