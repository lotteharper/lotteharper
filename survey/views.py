from django.contrib.auth.decorators import user_passes_test
from feed.tests import pediatric_identity_verified
from face.tests import is_superuser_or_vendor
from vendors.tests import is_vendor
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache

@login_required
@user_passes_test(pediatric_identity_verified, login_url='/verify/', redirect_field_name='next')
def has_completed_survey(request):
    from django.http import HttpResponse
    from .models import Survey, Answer
    for s in Survey.objects.all().order_by('priority'):
        a = Answer.objects.filter(survey=s, user=request.user, completed=True)
        if a.count() < 1:
            return HttpResponse('f')
    return HttpResponse('t')

@login_required
@user_passes_test(pediatric_identity_verified, login_url='/verify/', redirect_field_name='next')
def survey(request, id):
    from django.shortcuts import render, redirect, get_object_or_404
    from django.urls import reverse
    from users.models import Profile
    from django.contrib import messages
    from .forms import SurveyForm
    from django.http import HttpResponse
    from .models import Survey, Answer
    surv = get_object_or_404(Survey, id=id)
    answer = Answer.objects.filter(user=request.user, survey=surv, completed=False).first()
    if not answer: answer = Answer.objects.create(user=request.user, survey=surv, completed=False)
    answer.user = request.user
    answer.survey = surv
    answer.save()
    if request.method == 'POST':
        form = SurveyForm(request.POST, instance=answer, survey=surv)
        if form.is_valid():
            answer = form.save()
            answer.completed = True
            answer.save()
            for s in Survey.objects.all().order_by('priority'):
                a = Answer.objects.filter(survey=s, user=request.user, completed=True)
                if a.count() < 1:
                    return redirect(reverse('survey:survey', kwargs={'id': s.id}) + '?hidenavbar=t')
            return HttpResponse('You have finished the survey. You will be redirected soon, thank you for your input.')
        else: messages.warning(request, str(form.errors))
    return render(request, 'survey/survey.html', {
        'form': SurveyForm(survey=surv),
        'full': True
    })

@login_required
@user_passes_test(pediatric_identity_verified, login_url='/verify/', redirect_field_name='next')
def answer(request):
    from django.shortcuts import render, redirect
    from django.urls import reverse
    from .models import Survey, Answer
    next = request.GET.get('next')
    for s in Survey.objects.all().order_by('priority'):
        a = Answer.objects.filter(survey=s, user=request.user, completed=True)
        if a.count() < 1:
            return render(request, 'survey/answer.html', {
                'title': 'Survey',
                'survey': Survey.objects.all().order_by('priority').first(),
                'full': True
            })
        else: return redirect(next if next else reverse('landing:landing'))

@login_required
@user_passes_test(pediatric_identity_verified, login_url='/verify/', redirect_field_name='next')
@user_passes_test(is_superuser_or_vendor)
def update(request, id):
    from survey.forms import UpdateSurveyForm
    from django.contrib import messages
    from django.shortcuts import render, redirect, get_object_or_404
    from survey.models import Survey
    surv = None
    if id != 'new':
        surv = get_object_or_404(Survey, id=int(id))
    if request.method == 'POST':
        form = UpdateSurveyForm(request.POST, surv=None)
        if form.is_valid():
            surv = form.save()
            q = surv.question
            Survey.objects.filter(question=surv.question).exclude(id__in=[surv.id]).delete()
            messages.success(request, 'This survey was updated.')
            from django.urls import reverse
            return redirect(reverse('survey:update', kwargs={'id': surv.id}))
    print(surv)
    form = UpdateSurveyForm(surv=surv)
#initial={'priority': surv.priority, 'question': surv.question, 'answers_seperated': surv.answers_seperated}
    context = {
        'title': 'Update Survey',
        'form': form
    }
    return render(request, 'survey/update.html', context)

@login_required
@user_passes_test(pediatric_identity_verified, login_url='/verify/', redirect_field_name='next')
@user_passes_test(is_superuser_or_vendor)
def surveys(request):
    from django.shortcuts import render
    from .models import Survey
    thesurveys = Survey.objects.all().order_by('priority')
    return render(request, 'survey/surveys.html', {'surveys': thesurveys})
