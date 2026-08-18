from django import forms


class PunchOutForm(forms.Form):
    notes = forms.CharField(
        required=False, widget=forms.Textarea(attrs={"rows": 3}), max_length=2000
    )
