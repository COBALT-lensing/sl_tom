from django import forms


class TargetLookupForm(forms.Form):
    search = forms.CharField(
        widget=forms.TextInput(attrs={"placeholder": "Target or subject ID"})
    )
