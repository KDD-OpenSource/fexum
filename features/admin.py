from django.contrib import admin
from features.models import RelevancyResult, Feature, Dataset, RedundancyResult
from django import forms
from features.tasks import calculate_rar
import json


# TODO: Fix
#TODO: Search for wronc occureences of results

class RelevancyResultJsonForm(forms.ModelForm):
    relevany_result_json = forms.CharField(label='Relevancy Result as JSON', widget=forms.Textarea, required=True)
    target = forms.ModelChoiceField(queryset=Feature.objects.all(), required=True)

    class Meta:
        model = RelevancyResult
        fields = ['relevany_result_json', 'target']

    def clean(self):
        cleaned_data = super(RelevancyResultJsonForm, self).clean()
        relevany_result_json_text = cleaned_data['relevany_result_json']
        try:
            cleaned_data['relevany_result_json'] = json.loads(relevany_result_json_text)
        except Exception as error:
            raise forms.ValidationError('JSON Error: {0}'.format(error))
        return cleaned_data


class RelevancyResultJsonAdmin(admin.ModelAdmin):
    form = RelevancyResultJsonForm

    def save_model(self, request, obj, form, change):
        target = form.cleaned_data['target']
        relevany_result_json = form.cleaned_data['relevany_result_json']
        calculate_rar.delay(target_id=target.id, precomputed_data=relevany_result_json)


class RedundancyResultJsonForm(forms.ModelForm):
    redundancy_result_json = forms.CharField(label='Redudancy Result as JSON', widget=forms.Textarea, required=True)
    dataset = forms.ModelChoiceField(queryset=Dataset.objects.all(), required=True)

    class Meta:
        model = RedundancyResult
        fields = ['redundancy_result_json', 'dataset']

    def clean(self):
        cleaned_data = super(RedundancyResultJsonForm, self).clean()
        redundancy_result_json_text = cleaned_data['redundancy_result_json']
        try:
            cleaned_data['relevany_result_json'] = json.loads(redundancy_result_json_text)
        except Exception as error:
            raise forms.ValidationError('JSON Error: {0}'.format(error))
        return cleaned_data


class RedundancyResultJsonAdmin(admin.ModelAdmin):
    form = RedundancyResultJsonForm

    def save_model(self, request, obj, form, change):
        dataset = form.cleaned_data['dataset']
        redundancy_result_json = form.cleaned_data['redundancy_result_json']
        calculate_rar.delay(target_id=target.id, precomputed_data=redundancy_result_json)


admin.site.register(RelevancyResult, RelevancyResultJsonAdmin)
admin.site.register(RedundancyResult, RedundancyResultJsonAdmin)
