from django.shortcuts import render_to_response, redirect
# from django.http import HttpResponse, HttpResponseRedirect
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import auth
from django.template.loader import get_template
from django.template.context import Context, RequestContext
from django.utils.translation import ugettext as _
from django.core.mail import send_mail,EmailMessage,SMTPConnection
from django.contrib.sessions.models import Session
from erp_test.home.forms import *
from erp_test.misc.helper import *
import models,forms
from erp_test.misc.util import *
# Take care of session variable
from erp_test.home import models
from erp_test.users.models import *
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.tokens import default_token_generator
import sha, random, datetime
from django.http import Http404
def home(request):
    redirected = session_get (request,"from_url")
    access_denied = (request, "access_denied")
    logged_in = session_get (request, "logged_in")
    already_logged = session_get (request, "already_logged")
    return render_to_response('home/home.html', locals(), context_instance= global_context(request))

def login(request):
    redirected = request.session.get ("from_url", False)
    just_registered = session_get(request, "just_registered")
    form = forms.UserLoginForm ()
    print "just before if"
    if request.method == 'POST':
        print "in the login , it is post"
        data = request.POST.copy()

        form =forms. UserLoginForm (data)
	if form.is_valid():
            send_mail_curr_info (request, 'Before authentication')
            user = auth.authenticate(username=form.cleaned_data['username'],
                                     password=form.cleaned_data["password"])
            send_mail_curr_info (request, 'After authentication')
            if user is not None and user.is_active == True:
                auth.login (request, user)


                # WHERE THE HELL IS THIS USED?
                # url = session_get(request, "from_url")
                # # Handle redirection
                # if not url:
                #     url = "%s/home/"%settings.SITE_URL


                send_mail_curr_info (request, 'After Login')
                request.session['logged_in'] = True

                # try:
                #     response.set_cookie('logged_out', 0)
                # except:
                #     pass

                if redirected:
                    return redirect (redirected)
                else:
                    return redirect ('tasks.views.display_portal',
                                     owner_name = user.username)
            else:
                invalid_login_message="The details provided by you dont match , please try again "
                print "the user has not logged in -invalid "
                request.session['invalid_login'] = True
                print request.path
                return render_to_response('home/login.html', locals(), context_instance= global_context(request))

                # WTH is this?
                invalid_login =session_get(request, "invalid_login")
                form = forms.UserLoginForm ()
    else:
        pass

    return render_to_response('home/login.html', locals(), context_instance= global_context(request))

def logout (request):
    if request.user.is_authenticated():
        auth.logout (request)
        response= redirect ('home.views.home')
        try:
          #  response.set_cookie('unb_User',"")
            response.set_cookie('logged_out', 1)
        except:
            pass
        return response
    return render_to_response('home/home.html', locals(), context_instance= global_context(request))
    
    
    
    
def password_forgot(request):


    if request.method == 'POST':
        data = request.POST.copy()
        form =forms.forgot_password_form(data)
        print "checking details for forgot_password"
        if form.is_valid():
            if True:
                print "the givrn form is awesome"
                salt = sha.new(str(random.random())).hexdigest()[:5]
#                print "one"
                activation_key = sha.new(salt+form.cleaned_data['username']).hexdigest()
#                print "two"
                print activation_key
                
                print form.cleaned_data['email_id'] , "is the username entered"
                user=User.objects.get(username=form.cleaned_data['username'] , email=form.cleaned_data['email_id'])
                print "the user with this name and emailid exists "
                invalid_login_message ="such and such a username exists dotn worry"
                # here to send email to the coord
                coordname=form.cleaned_data['username']
                hyperlink=settings.SITE_URL+"/home"+"/change_password/"+activation_key+"/"+coordname
                print hyperlink
                mail_header="follow the link and change your password , once you log in"
                email_id=form.cleaned_data['email_id']
                mail=[email_id,]
                invalid_message="if it stops here there is some problem in getting mail template"
                mail_template=get_template("home/forgot_password_mail.html")
                invalid_login_message ="We have tried to mail you but then there is some internal problem ,get_template works"
                body=mail_template.render(Context({'coordname':coordname,
                                                   'SITE_URL':hyperlink,
                                                   'new_password':"password",
                                                   }))
                password_object=forgot_password.objects.create(username=coordname ,email_id=email_id,activation_key=activation_key ,date=datetime.datetime.now())
                invalid_message="body ban gayi , send_mail mai gadbad"
                send_mail(mail_header,body,'noreply@shaastra.org',mail,fail_silently=False)
                #message=mail_coord(hyperlink ,mail_header ,coordname ,  "home/forgot_password_mail.html",mail)
                invalid_login_message ="We have mailed you your new password if any further problem contact the webops dept"                
                form = forms.UserLoginForm ()
                return render_to_response('home/login.html', locals(), context_instance= global_context(request))
        """
            except:
                pass #invalid_login_message= "details given by u dont match , please for further clarification contact webops  dept"
             """
    else:
        print "problem in forgot_password_view"
    forgot_form=forgot_password_form()
    return render_to_response('home/forgot_password.html', locals(), context_instance= global_context(request))
    
        
def change_password(request ,activation_key=None ,username=None) :
    print "in change_password view"
    if request.method == 'POST':
        print "the data is post"
        data = request.POST.copy()
        form =forms. Change_password(data)

        if form.is_valid():
            print "the data is valid"
            password=form.cleaned_data['password']
            password_again=form.cleaned_data['password_again']

            print username
	    if(password==password_again):
	        message="done"
	        print username
		user_object=User.objects.get(username=username)
		
		print "object exixts"
		email_id=user_object.email
		user_object.set_password(password)
		user_object.save()
		print email_id
		print user_object	        
	    else:
	        message="The password do not match"
            print password
            print password_again
        else:
            print form.errors
            print "The change password form is not valid"
        
    else:   
	    try:
		print "not post"
		password_change=forgot_password.objects.get(activation_key=activation_key )
		print "there is such actiatin key"
		user1 =User.objects.get(username=username)
		#If it comes till here it has passed the test and sucha user exists who wants to change his password
	   	print "the user name and stuff match"	
	   	Change_password=forms.Change_password()
	   	print Change_password
	     	return render_to_response('home/change_password.html', locals(), context_instance= global_context(request))    
	     	

	    except:
		print "either there is an error or wrong link"
    form = forms.UserLoginForm () 
    return redirect ('home.views.login')   		
#    return render_to_response('home/login.html', locals(), context_instance= global_context(request))    



def reset_password(request): 
   if request.method == 'POST':
        form = forms.ResetPasswordForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data['password']
            
            try:
                user=request.user
                user.set_password(password)
                user.save()
                return redirect('home/login.html', locals(), context_instance = global_context(request))
            except User.DoesNotExist:
                raise Http404
        else:
           return redirect('home/login.html', locals(), context_instance=global_context(request))
   else:
       form=forms.ResetPasswordForm(request.POST)   
       return render_to_response('home/reset_password.html', locals(), context_instance = global_context(request))

"""
def forgot_password(request):

    forgot_form=forgot_password_form()

    if request.method == 'POST':
        print "the data is post"
        data = request.POST.copy()
        form =forms. Change_password(data)

        if form.is_valid():
            print "the data is valid"
            password=form.cleaned_data['password']
            password_again=form.cleaned_data['password_again']

            print username
	    if(password==password_again):
	        message="done"
	        print username
		user_object=User.objects.get(username=username)
		
		print "object exixts"
		email_id=user_object.email
		user_object.set_password(password)
		user_object.save()
		print email_id
		print user_object	        
	    else:
	        message="The password do not match"
            print password
            print password_again
        else:
            print form.errors
            print "The change password form is not valid"
        
    else:   
	    try:
		print "not post"
		password_change=forgot_password.objects.get(activation_key=activation_key )
		print "there is such actiatin key"
		user1 =User.objects.get(username=username)
		#If it comes till here it has passed the test and sucha user exists who wants to change his password
	   	print "the user name and stuff match"	
	   	Change_password=forms.Change_password()
	   	print Change_password
	     	return render_to_response('home/change_password.html', locals(), context_instance= global_context(request))    
	     	

	    except:
		print "either there is an error or wrong link"
    form = forms.UserLoginForm () 
    return redirect ('home.views.login')   		
#    return render_to_response('home/login.html', locals(), context_instance= global_context(request))    


    """
    
    
