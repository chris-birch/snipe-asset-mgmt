from django.shortcuts import render

from .models import Asset_Models

import requests
import json
import re

from pprint import pprint
from deepdiff import DeepDiff


BASE_API_URL = 'https://lululemon.snipe-it.io/api/v1/'
API_KEY = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiIxIiwianRpIjoiMjRjMzFlM2YwM2U3ZDY5N2M2OTA0M2ZjNWQ5ZDQ5ZDRmMjc2MWE2YWIyMWQ0NWQwMmQzZjEzZDkyODg5ZTA4Mjk1NjVmM2U4ZDU4MzY3ZDAiLCJpYXQiOjE2MTAxMjY1NjUsIm5iZiI6MTYxMDEyNjU2NSwiZXhwIjoyMjQxMjc4NTY1LCJzdWIiOiIxIiwic2NvcGVzIjpbXX0.TiiH3SvsZGcffILLc_DH6t4nTvO1oRwMI-7fQoPmSCzJ-I3k9NeZIx0KFRwVWSmfzVf7sfYuo_6TYo4kzKvIXucDERq_i4FO8Di2pGE-si_ARhh_dGRofYNmlzAKsoJICLKM-ViuzlFsa7Jkfm4ZmWyqHZU6JSfTKNPsVNQ6_Ind2xt0oKd5RDD95tdLUOhHF1Txu0bOT0mNtHrq6flQepm7Rli5JLqqzFFckJvETiTW6ZxqtUUM0GyZX-kdjJsREJi5Gi9S8zROuv55UWWIIVBtmkVBqScJAeBIfxKPzKQADY8qQCwiTYv_xsVgd_URpT-WLrCVS5oILTHTG_CBf4V5S9tIC_UkqUx5jY6-2scOp4IgMy_S4OByoOGtZLf20tXY34wIjOZdSGQRNR7GIpuj8ha_lWlhjginARUy8duIBxHXGMwxY2GhnDs376YG6yuMgAezDS4oZ-seUWMXwUqOAmFyfY22EmplwOkFrm2-s6sPtB7T5taaaPm1ZXdM3l6Hm1CjsJuETyMG19vMIkhnWZDsoD9zzxkN8K8oMf_bWpJYKYxcfZvsde-FMRZaTMeSn-4JchO67yKxtmOiioPXBc6Ix545SkGOikmFf_EhXhSUPKmgJ5pGeX4iPkay-40FiM0gtGx18UDdZ45Mo0SyBuvAzOOlFus0g_1YAtg'

def SnipeApi(api_resource):

    headers = {"Authorization": "Bearer " + API_KEY}
    querystring = {"limit":"500", "offset":"0"}
    url = BASE_API_URL+api_resource

    r = requests.get(url, headers=headers, params=querystring)

    # Check if the HTML login screen is being returned
    if '<!DOCTYPE html>' in r.text:
        return json.dumps({"error": "API Authentication fail"})
    else:
        return r.json()

def getSnipeModles():
    api_model_data = SnipeApi('models')

    snipeAssetIDs = []

    # The API limit on the AWS hosted server is 120 per min so don't want to paginate
    if api_model_data['total'] > int(500):
        return json.dumps({"error": "There are more than 500 asset models. The API can't handle this"})


    # Get existing asset models from the database
    db_asset_models = Asset_Models.objects.all()

    for each_asset_model in api_model_data['rows']:

        # Add the snipe ID list to check against later
        snipeAssetIDs.append(each_asset_model['id'])
        
        # Cretae an asset data model dict from the JSON data
        snipe_asset_model = {}
        snipe_asset_model['snipe_model_id'] = int(each_asset_model['id'])
        snipe_asset_model['model_name'] = each_asset_model['name']
        snipe_asset_model['model_manufacturer_name'] = each_asset_model['manufacturer']['name']
        snipe_asset_model['model_number'] = each_asset_model['model_number']
        snipe_asset_model['model_category'] = each_asset_model['category']['name']
        snipe_asset_model['model_count'] = each_asset_model['assets_count']

        # 
        # START DATA CHECKS
        #

        ### Add any new Snipe asset models to the database ###
        if each_asset_model['id'] not in db_asset_models.values_list('snipe_model_id', flat=True):
            
            new_asset_model = Asset_Models()
            new_asset_model.snipe_model_id = snipe_asset_model['snipe_model_id']
            new_asset_model.model_name = snipe_asset_model['model_name']
            new_asset_model.model_manufacturer_name = snipe_asset_model['model_manufacturer_name']
            new_asset_model.model_number = snipe_asset_model['model_number']
            new_asset_model.model_category = snipe_asset_model['model_category']
            new_asset_model.model_count = snipe_asset_model['model_count']
            new_asset_model.model_min_qty = int(0)
            new_asset_model.save()
            continue

        ### Check for any changed data, update the database ###
        db_id = db_asset_models.filter(snipe_model_id=each_asset_model['id']).values_list('id', flat=True)[0]
        db_data = db_asset_models.filter(snipe_model_id=each_asset_model['id']).values()[0]
        diff_result = DeepDiff(db_data, snipe_asset_model)

        if 'values_changed' in diff_result:
            
            new_asset_model = Asset_Models.objects.get(id=int(db_id))
            
            # Setup an empty dict we can add db updates to
            data_to_save = {}
            
            for field, value in diff_result['values_changed'].items():
                
                # Get the db field name we want to update from the DeepDiff results
                db_field_name = re.search("\[\'(.+?)\'\]", str(field)).group(1)
                
                # Load the dict we crated before with updated data
                data_to_save[db_field_name] = snipe_asset_model[db_field_name]
            
            # Prime the Django asset model with the updated data
            new_asset_model.__dict__.update(data_to_save)
            
            try:
                new_asset_model.save()
            except:
                print("FAIL: " + each_asset_model['name'])
            else:
                print("SECCSESS: " + each_asset_model['name'])

            continue


    ### Check for deleted asset models, remove from the database ###
    db_data = list(db_asset_models.values_list('snipe_model_id', flat=True))
    diff_result = DeepDiff(db_data, snipeAssetIDs, ignore_order=True)

    if 'iterable_item_removed' in diff_result:
        
        for item, snipe_asset_id in diff_result['iterable_item_removed'].items():

            deleted_asset_model = Asset_Models.objects.get(snipe_model_id=int(snipe_asset_id))
            deleted_asset_model.delete()

    return db_asset_models



def index(request):
    populateReportTable()
    snipe_models = getSnipeModles()
    context = {'snipe_models': snipe_models}
    return render(request, 'min_asset_levels/index.html', context)