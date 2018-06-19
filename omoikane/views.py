from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext, loader
from django.shortcuts import redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import UserCreationForm


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            new_user = authenticate(username=request.POST["username"],
                                    password=request.POST["password1"])
            login(request, new_user)
            return HttpResponseRedirect("/quiz")
    else:
        form = UserCreationForm()

    template = loader.get_template('registration/register.html')
    return HttpResponse(template.render({'form': form}, request))
