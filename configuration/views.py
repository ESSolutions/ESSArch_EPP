# Create your views here.
from django.template import Context, loader
from django.template import RequestContext 
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect
from django import forms
from django.shortcuts import render_to_response
from django.core.context_processors import csrf
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import logout
from django.contrib.auth.views import password_change as admin_password_change

from configuration.models import Parameter, LogEvent, InfoXML

from parametersform import ParametersForm
from logeventform import LogEventForm

import sys

@login_required
def index(request):
    t = loader.get_template('index.html')
    c = RequestContext(request)
    return HttpResponse(t.render(c))

def logout_view(request):
    logout(request)
    # Redirect to a success page.
    return HttpResponseRedirect( '/' )

@login_required
def change_password(request):
    return admin_password_change( request, post_change_redirect="/" )


@staff_member_required
def logevents( request ):
    allevents = LogEvent.objects.all()
    c = { 'logevent_list':allevents }
    return render_to_response('configuration/logevents.html', c, 
                              context_instance=RequestContext(request) )


@staff_member_required
def newlogevent(request):
    le = LogEvent()
    le.save()
    return HttpResponseRedirect( '/configuration/logevents/%d' % le.id )


@staff_member_required
def installlogdefaults(request):
    eventType_keys = {
        1:['Leveransen forbereds og genereras','10000'],
        2:['Leverans sker','10001'],
        3:['Mottagning av leverans','10002'],
        4:['Overlamning av leverans','10003'],
        5:['Mottagning av leverans','10004'],
        6:['Registrering av leverans','10005'],
        7:['Journalforing i journalsystem','10006'],
        8:['Registrering i arkivsystem','10007'],
        9:['Mottakskvittering sendes','10008'],
        10:['Skapa loggcirkular','10009'],
        11:['UUID skapas for leverans','10010'],
        12:['Skapa AIC_UUID katalogstruktur','10011'],
        13:['Loggcirkular skapas under AIC_UUID','10012'],
        14:['Viruskontroll','10013'],
        15:['Leveransen kontrolleras','10014'],
        16:['Overlamning av leverans','10015'],
        17:['Mottagning av leverans','10016'],
        18:['Overlamning av leverans','10017'],
        19:['Bearbeiding av katalogstruktur IP','10144'],
        20:['Utpakking av materialet','10145'],
        21:['Testing av materialet','10146'],
        22:['Endring i materialet','10147'],
        23:['Innhenting av tilleggsinformasjon','10148'],
        24:['Endring av metadata','10149'],
        25:['Brev till arkivskaper','10150'],
    }
    for key in eventType_keys:
        print >> sys.stderr, "**", key
        try:
            le = LogEvent( eventType=eventType_keys[key][1],
                           eventDetail=eventType_keys[key][0] )
            le.save()
        except:
            pass
    return HttpResponseRedirect( '/' )

@staff_member_required
def deletelogevent( request, eventId ):
    LogEvent.objects.filter( id=eventId ).delete()
    return HttpResponseRedirect( '/configuration/logevents' )


@staff_member_required
def editlogevent( request, eventId ):
    if request.method == 'POST': # If the form has been submitted...
        form = LogEventForm(request.POST) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
            # Process the data in form.cleaned_data
            # ...
            objs = LogEvent.objects.filter( id=eventId )
            if len( objs ) > 0:
                le = objs[0]
            else:
                le = LogEvent()
            le.populate_from_form( form )
            le.save()

            return HttpResponseRedirect( '/configuration/logevents' )
        else:
            c = { 'form': form, 'id':eventId }
            c.update(csrf(request))
            return render_to_response('configuration/editlogevent.html', c, 
                                      context_instance=RequestContext(request) )
    else:
        objs = LogEvent.objects.filter( id=eventId )
        if len( objs ) > 0:
            le = objs[0]
        else:
            le = LogEvent()
            le.username = username
        form = LogEventForm(initial=le.get_value_array()) # Form with defaults

    c = { 'form': form, 'id':eventId }
    c.update(csrf(request))

    return render_to_response('configuration/editlogevent.html', c, context_instance=RequestContext(request) )




@staff_member_required
def parameters( request ):
    allusers = User.objects.all()
    c = { 'allusers':allusers }
    return render_to_response('configuration/parameters.html', c, 
                              context_instance=RequestContext(request) )

@staff_member_required
def userparameters( request, username ):
    #if not request.user.is_authenticated():
    #    return HttpResponseRedirect('/login/?next=%s' % request.path)
    
    if request.method == 'POST': # If the form has been submitted...
        form = ParametersForm(request.POST) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
            # Process the data in form.cleaned_data
            # ...
            objs = Parameter.objects.filter( username=username )
            if len( objs ) > 0:
                p = objs[0]
            else:
                p = Parameter()
                p.username = username
            p.populate_from_form( form )
            p.save()

            c = { 'form': form, 'message':"Settings saved...", 
                  'username':username }
            c.update(csrf(request))
            return render_to_response('configuration/userparameters.html', c, 
                                      context_instance=RequestContext(request) )
        else:
            c = { 'form': form, 'username':username }
            c.update(csrf(request))
            return render_to_response('configuration/userparameters.html', c, 
                                      context_instance=RequestContext(request) )
    else:
        objs = Parameter.objects.filter( username=username )
        if len( objs ) > 0:
            p = objs[0]
        else:
            p = Parameter()
            p.username = username
        form = ParametersForm(initial=p.get_value_array()) # Form with defaults

    c = { 'form': form, 'username':username }
    c.update(csrf(request))

    return render_to_response('configuration/userparameters.html', c, 
                              context_instance=RequestContext(request) )


