from django import forms
from . import models


class SearchForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(SearchForm, self).__init__(*args, **kwargs)
        fields = {
            'Gender': ('Mens','Womens'),
            'Waist Size': ('26','27','28','29','30','31','32','33','34','35','36','37','38','40','42','46','48','50'),
            'Inside Leg': ('24','26','28','30','32','34','36','38'),
            'Style': ('Straight','Slim','Skinny','Relaxed','Regular','Flared','Classic','Bootcut','Tapered','Wide-Leg'),
            'Brand': ('7 for All Mankind','AllSaints','Citizens of Humanity','Diesel','EDWIN','G-Star','HUGO','Levis','Nudie','Replay','SuperDry','Tommy Hilfiger'),
            'Colour': ('Black','Blue','Grey'),
            'Condition': ('Used','New','New with Tags'),
            'Closure': ('Zip','Button')
        }
        checklist_dict = {}
        for name,values in fields.items():
            checklist_dict[name] = forms.ModelChoiceField(queryset=models.Jean.objects.all(), label=name, required=False)

    def clean_data(self):
        return self.cleaned_data
 
    def save(self, commit=True):
        user = super(SearchForm, self).save(commit=False)
        user.gender = self.cleaned_data["gender"]
        user.waist_size = self.cleaned_data["waist_size"]
        user.inside_leg = self.cleaned_data["inside_leg"]
        if commit:
            user.save()
        return user
