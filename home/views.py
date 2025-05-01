from django.shortcuts import render
from .models import Profile, Skill, Link, Contact

def index(request):
    try:
        profile = Profile.objects.first()
    except:
        profile = None
        
    context = {
        'profile': profile,
        'skills': Skill.objects.all(),
        'nav_links': Link.objects.filter(is_navigation=True),
        'social_links': Link.objects.filter(is_navigation=False),
        'contacts': Contact.objects.all(),
    }
    return render(request, 'home/index.html', context)