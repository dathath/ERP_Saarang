from django.contrib import auth
from django.shortcuts import render_to_response, redirect
from django.template.loader import get_template
from django.template.context import Context, RequestContext
from erp_test.tasks.models import Task, SubTask
from erp_test.users.models import *
from erp_test.misc.helper import *
from erp_test.misc.helper_2 import *
from erp_test import settings
from erp_test.users import models
from django.core.mail import send_mail,EmailMessage,SMTPConnection
import os # upload files
import MySQLdb
import re, md5, time
from erp_test.tasks.models import SubTask ,Task

# Some macros for readability
NORMAL = 1
FILE = 2
MCQ = 3
MESSAGE = 4

# Generates a context with the most used variables
def global_context(request):
    # The try...except blocks are there for the case when an anonymous
    # user visits any page (esp the login page)
    try:
        user_dept_name = request.user.get_profile ().get_dept ().name
    except:
        user_dept_name = False
    try:
        user_name = request.user.get_profile ().name
    except:
        user_name = False

    try:
        photo_list=give_photo_array()
#        for field in photo_list:
#            print field ,"\n\n"
        print "photos are there"          
    except:
        pass

    page_owner = request.session.get ('page_owner', request.user)
    print "the paghe owner in util is" ,page_owner
    try:
        po_dept_name = page_owner.get_profile ().get_dept ().name
    except:
        po_dept_name = False

    try:
        po_name = page_owner.get_profile ().name
    except:
        po_name = False

    if page_owner != request.user:
        is_visitor = True
    else:
        is_visitor = False
    try:
        calendar_complete_data ,now ,month_name=calendar_right_bottom(request,page_owner,Task)
        print "calndar data successfully got"
	pass
	
    except:
        calendar_complete_data=[]
        month_name=[]
        print "there is problem with the bottom calendar thing , bring into notice"
        
    try:
        year_2=now.year
        month_2=now.month
    except:
        year_2="2011"
        month_2="August"
    context =  RequestContext (request,
            {'user':request.user,
             'request' : request,
            'SITE_URL':settings.SITE_URL,
             'user_dept_name': user_dept_name,
             'user_name': user_name,
             'is_core' : is_core (request.user),
             'is_coord' : not is_core (request.user),
             'po_is_core' : is_core (request.user),
             'po_is_coord' : not is_core (request.user),
             'is_visitor' : is_visitor,
             'page_owner' : page_owner,
             'po_name' : po_name,
             'po_dept_name' : po_dept_name,
             'photo_main_list':photo_list,
             'calendar_complete_data':calendar_complete_data,
             'year_2':year_2,
            'month_2':month_2,
            'month_names':month_name,

            })
    return context

# Error pages
def not_found (request):
    return render_to_response('404.html', locals(), context_instance= global_context(request)) 
def server_error (request):
    return render_to_response('500.html', locals(), context_instance= global_context(request)) 


# Convert Foo Contest <-> FooContest
def camelize (str):
    return str.replace (' ','')
def decamelize (str):
    p = re.compile (r'([A-Z][a-z]*)')
    result = ''
    for blob in p.split (str):
        if blob != '':
            result += blob + ' '
    return result[:-1]

# Take care of session variable
# Note : This will pop the key from request.session
def session_get (request, key, default=False):
    value = request.session.get (key, False)
    if value:
        pass
        del request.session[key]
    else: 
        value = default
    return value


# Decorators

# Force authentication first
def needs_authentication (func):
    # print 'In Decorator - Function Name : ', func.__name__
    def wrapper (*__args, **__kwargs):
        request = __args[0]
        send_mail_curr_info (request, 'In needs_authentication')
        if not request.user.is_authenticated():
            # Return here after logging in
            request.session['from_url'] = request.path
            send_mail_curr_info (request, 'After being un-authenticated')
            print "path from util", request.path
            return redirect (settings.SITE_URL+"/participant/login")
        else:
            return func (*__args, **__kwargs)
    return wrapper


# For urls that can't be accessed once logged in.
def no_login (func):
    def wrapper (*__args, **__kwargs):
        request = __args[0]
        if request.user.is_authenticated():
            # Return here after logging in
            request.session['already_logged'] = True
	    #html = "%s/home/" %SITEURL
            return redirect ('home.views.home')
        else:
            return func (*__args, **__kwargs)
    return wrapper

# TODO : decorator
def page_owner_only (alternate_view_name = '', **kwargs):
    """
    Based on the view name, decide which wrapper to return.

    Edit Task / SubTask:
    If user is not of the same department as the task, then just
    display the task, etc.
    If Task does not exist, redirect.

    General view:
    If page owner != current user, redirect to alternate_view_name and
    pass kwargs.
    """
    def _dec(func):
        def edit_task_wrapper (*__args, **__kwargs):
            request = __args[0]
            curr_task_id = __kwargs.get('task_id', None)
            curr_page_owner = User.objects.get(
                username = __kwargs.get('owner_name', None))
            if curr_task_id is None:
                # Creation of Task
                if is_core (request.user):
                    if request.user == curr_page_owner:
                        # Go ahead
                        return func (*__args, **__kwargs)
                    else:
                        # You can't create Tasks while visiting some
                        # other user's pages
                        # (use case : manually typing erp_test/coord_name/edit/)
                        print 'Go create Tasks in your own page, dude.'
                        print 'Redirecting... to visited User\'s portal'
                        return redirect (
                            'erp_test.tasks.views.display_portal',
                            owner_name = __kwargs.get('owner_name',
                                                      request.user.username))
                else:
                    # User is not a Core
                    print 'You aren\'t authorized to create Tasks.'
                    print 'Redirecting... to visited User\'s portal'
                    return redirect ('tasks.views.display_portal',
                                     owner_name = __kwargs.get('owner_name',
                                                               request.user.username))
            return handle_existing_object (Task, curr_task_id,
                                           request.user, curr_page_owner,
                                           func, __args, __kwargs)

        def edit_subtask_wrapper (*__args, **__kwargs):
            request = __args[0]
            curr_subtask_id = __kwargs.get('subtask_id', None)
            curr_page_owner = User.objects.get(
                username = __kwargs.get('owner_name', None))
            return handle_existing_object (SubTask, curr_subtask_id,
                                           request.user, curr_page_owner,
                                           func, __args, __kwargs)

        def simple_wrapper (*__args, **__kwargs):
            """
            Just check that the page owner and the curr user are the same.
            """
            request = __args[0]
            curr_page_owner = User.objects.get(
                username = __kwargs.get('owner_name', None))

            if curr_page_owner != request.user:
                # Call the alternate view with the keyword args passed
                # to the decorator.
                return redirect (alternate_view_name, **kwargs)
            else:
                return func (*__args, **__kwargs)

        # Decide which function to return based on the view being decorated
        if func.__name__ == 'edit_task':
            return edit_task_wrapper
        elif func.__name__ == 'edit_subtask':
            return edit_subtask_wrapper
        else:
            return simple_wrapper	
    return _dec


def handle_existing_object (Model, object_id, curr_user,
                            curr_page_owner, func, __args, __kwargs):
    """
    If object of model 'Model' does not exist, redirect to user portal.
    Else, if curr_user is an owner of the model and is in his own
    page, let him edit it.
    Or else, simply display the object.
    """
    model_name = Model.__name__.lower ()
    print 'Curr ', model_name, ' id : ', object_id
    try:
        curr_object = Model.objects.get (id = object_id)
    except:
        print model_name, ' with id : ', object_id, ' does not exist.'
        print 'Redirecting... to visited User\'s portal'
        return redirect ('tasks.views.display_portal',
                         owner_name = __kwargs.get('owner_name',
                                                   curr_user.username))
    else:
        # Only the owner(s) can edit the object and that too only in
        # their own page
        if model_name == 'task' and curr_object.is_owner (curr_page_owner) and curr_user == curr_page_owner:
            # User can edit the object in his own page
            return func (*__args, **__kwargs)
        if model_name == 'subtask' and (curr_object.is_owner (curr_page_owner) or curr_object.is_assignee (curr_page_owner)) and curr_user == curr_page_owner:
            # User can edit the object in his own page
            return func (*__args, **__kwargs)
        # View Name
        my_pos_args = ['erp_test.tasks.views.display_' + model_name]
        # Arguments to be passed to the view
        my_kw_args = {model_name + '_id' : object_id,
                      'owner_name' : __kwargs.get('owner_name',
                                                  curr_user.username)}
        return redirect (*my_pos_args, **my_kw_args)
