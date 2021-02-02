from django import forms

class EditMinQty(forms.Form):
    min_qty = forms.IntegerField(required=True, label='Minimum asset Quantity Level')
