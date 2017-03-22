from django.contrib import admin
from features.models import RarResult, Feature
from django import forms
from features.tasks import calculate_hics
import json


class RarResultJsonForm(forms.ModelForm):
    rar_result_json = forms.CharField(label='Rar Result as JSON', widget=forms.Textarea, required=True)
    target = forms.ModelChoiceField(queryset=Feature.objects.all(), required=True)

    class Meta:
        model = RarResult
        fields = ['rar_result_json', 'target']

    def clean(self):
        cleaned_data = super(RarResultJsonForm, self).clean()
        rar_result_json_text = cleaned_data['rar_result_json']
        try:
            cleaned_data['rar_result_json'] = json.loads(rar_result_json_text)
        except Exception as error:
            raise forms.ValidationError('JSON Error: {0}'.format(error))
        return cleaned_data


class RarResultJsonAdmin(admin.ModelAdmin):
    form = RarResultJsonForm

    def save_model(self, request, obj, form, change):
        target = form.cleaned_data['target']
        rar_result_json = form.cleaned_data['rar_result_json']
        calculate_hics.delay(target_id=target.id, precomputed_data=rar_result_json)


admin.site.register(RarResult, RarResultJsonAdmin)
