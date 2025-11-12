from django import forms
from .models import Survey, Answer
from feed.middleware import get_current_user

class UpdateSurveyForm(forms.ModelForm):
    question = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}))
    def __init__(self, *args, **kwargs):
        surv = kwargs.pop('surv', None)
        super(UpdateSurveyForm, self).__init__(*args, *kwargs)
#        if ins:
        from feed.middleware import get_current_request
        r = get_current_request()
        from translate.translate import translate
        self.fields['priority'].label = translate(r, 'Indexing priority', src='en')
        self.fields['question'].label = translate(r, 'A question to ask the visitor', src='en')
        self.fields['answers_seperated'].label = translate(r, 'Answers for the question, one per line', src='en')
        if surv:
            self.fields['priority'].initial = surv.priority
            self.fields['question'].initial = surv.question
            self.fields['answers_seperated'].initial = surv.answers_seperated

    class Meta:
        model = Survey
        fields = ('priority', 'question', 'answers_seperated')

class SurveyForm(forms.ModelForm):
    answer = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'survey-large-text'}),
    )
    def __init__(self, *args, **kwargs):
        surv = kwargs.pop('surv', None)
        super(SurveyForm, self).__init__(*args, *kwargs)
        from feed.middleware import get_current_request
        r = get_current_request()
        from translate.translate import translate
        from django.conf import settings
        self.fields['answer'].label = translate(r, surv.question, src=settings.DEFAULT_LANG)
        choices = ()
        self.instance.user = r.user
        self.instance.survey = surv
        survs = surv.answers_seperated.split('\n')
        survs[len(survs)-1]+='\n'
        for c in survs:
            choices+=((c[:-1], translate(r, c[:-1], src=settings.DEFAULT_LANG)),) #
        print(choices)
        self.fields['answer'].choices = choices

    class Meta:
        model = Answer
        fields = ('answer',)
