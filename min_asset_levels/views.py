from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.db.models import F
from .models import Asset_Models, Asset_Report
from .forms import EditMinQty
from django.contrib.auth.decorators import login_required

import requests
import json
import re

from requests.exceptions import HTTPError
from pprint import pprint
from deepdiff import DeepDiff


BASE_API_URL = 'https://lululemon.snipe-it.io/api/v1/'

# The SNIPE_API_KEY is in settings.py
def SnipeApi(api_resource, params):

    headers = {"Authorization": "Bearer " + SNIPE_API_KEY}
    querystring = {**params, "limit":"500", "offset":"0"}
    url = BASE_API_URL+api_resource

    try:
        r = requests.get(url, headers=headers, params=querystring)
        
        # If the response was successful, no Exception will be raised
        r.raise_for_status()
    
    except HTTPError as http_err:
        raise HTTPError('HTTP error occurred', http_err)

    except Exception as err:
        raise Exception('HTTP error occurred', err)

    else:
        # Check if the HTML login screen is being returned
        if '<!DOCTYPE html>' in r.text:
            raise Exception("Error: API Authentication fail")
        else:
            return r.json()


def getSnipeModles():
    
    try:
        api_model_data = SnipeApi('models', {})
    
    except Exception as error:
            return json.dumps({"error": str(error.args)})

    return_output = {}
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

            if 'new_asset_model' not in return_output:
                return_output['new_asset_model'] = {}

            return_output['new_asset_model'][snipe_asset_model['snipe_model_id']] = snipe_asset_model['model_manufacturer_name'] + " " + snipe_asset_model['model_name'] + " " + snipe_asset_model['model_number']

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
            
            new_asset_model.save()

            if 'updated_asset_model' not in return_output:
                return_output['updated_asset_model'] = {}

            return_output['updated_asset_model'][snipe_asset_model['snipe_model_id']] = snipe_asset_model['model_manufacturer_name'] + " " + snipe_asset_model['model_name'] + " " + snipe_asset_model['model_number']

            continue


    ### Check for deleted asset models, remove from the database ###
    db_data = list(db_asset_models.values_list('snipe_model_id', flat=True))
    diff_result = DeepDiff(db_data, snipeAssetIDs, ignore_order=True)

    if 'iterable_item_removed' in diff_result:
        
        for item, snipe_asset_id in diff_result['iterable_item_removed'].items():

            deleted_asset_model = Asset_Models.objects.get(snipe_model_id=int(snipe_asset_id))

            if 'deleted_asset_model' not in return_output:
                return_output['deleted_asset_model'] = {}
            
            return_output['deleted_asset_model'][snipe_asset_id] = deleted_asset_model.model_manufacturer_name + " " + deleted_asset_model.model_name + " " + deleted_asset_model.model_number

            deleted_asset_model.delete()    

    return return_output

#
# !!! This is a long running db & API query and should only be run as needed !!!
#
def populateReportTable():
    return_output = {}

    db_asset_models = Asset_Models.objects.all()

    # Empty the report table ready for new data
    Asset_Report.objects.all().delete()       

    # Asset models in the db, the API asset data
    for each_db_asset_model in db_asset_models.values():

        old_rtd_qty = each_db_asset_model['model_count_RTD']

        querystring = {"model_id":each_db_asset_model['snipe_model_id'],"status":"RTD"}

        try:
            api_data = SnipeApi('hardware', querystring)
    
        except Exception as error:
            return json.dumps({"error": str(error.args)})

        if api_data:
            
            # Update the asset model Ready_To_Deploy anount in the db
            db_asset_models.filter(id=each_db_asset_model['id']).update(model_count_RTD=int(api_data['total']))

            new_rtd_qty = api_data['total']
            
            if 'model_count_RTD' not in return_output:
                return_output['model_count_RTD'] = {}
            
            return_output['model_count_RTD'][each_db_asset_model['id']] = each_db_asset_model['model_manufacturer_name'] + " " + each_db_asset_model['model_name'] + " " + each_db_asset_model['model_number'], {'qty' : {'old': old_rtd_qty, 'new': new_rtd_qty}}

            # Get the asset info where we have it in the API
            if api_data['total'] > 0:

                for each_api_asset in api_data['rows']:
                    
                    # Find the asset's location or set 'unknown'
                    if each_api_asset['rtd_location']:
                        location = each_api_asset['rtd_location']['name']                         
                    elif each_api_asset['location']:                     
                        location = each_api_asset['location']['name']                  
                    else:
                        location = 'Unknown'

                    db_asset_report_model = {}
                    db_asset_report_model['asset_model_id'] = each_db_asset_model['id']
                    db_asset_report_model['model_location'] = location
                    db_asset_report_model['model_custom_fields'] = each_api_asset['custom_fields']
                    db_asset_report_model['model_asset_id'] = each_api_asset['asset_tag']

                    # Instantiate the Asset_Report() db model
                    new_asset_report_model = Asset_Report()

                    # Prime the Django asset model with the updated data
                    new_asset_report_model.__dict__.update(db_asset_report_model)
                    
                    new_asset_report_model.save()

        else:
            return json.dumps({"error": "No data returned from the API"})
    
    return return_output

@login_required
def index(request):
    db_Asset_Models = Asset_Models.objects.all()

    context = {'asset_model': db_Asset_Models}
    return render(request, 'min_asset_levels/index.html', context)

@login_required
def assetModelData(request):
    # Run the getSnipeModles(), return error if fail
    getSnipeModles()
    db_Asset_Models = Asset_Models.objects.all().values()
    db_Asset_Models_list = list(db_Asset_Models)
    data = json.dumps(db_Asset_Models_list)

    return HttpResponse(data, content_type="application/json")

@login_required
def minQtyUpdate(request, pk=0):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        try:
            AssetModel = Asset_Models.objects.get(id=pk)
        except:
            raise Http404("Asset does not exist")

        # create a form instance and populate it with data from the request:
        form = EditMinQty(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            AssetModel.model_min_qty = form.cleaned_data['min_qty']
            AssetModel.save()

            http_data = json.dumps({"success": "Asset Model Saved"})
            return HttpResponse(http_data, content_type="application/json")

    # if a GET (or any other method) we'll create a blank form
    else:
        form = EditMinQty()

    return render(request, 'min_asset_levels/EditMinQtyForm.html', {'form': form})

def html_asset_report(request):
    if request.user.is_authenticated:
        # Update the Report Data with the latest data from Snipe
        populateReportTable()

        # Get the data from the db ready to send to the HTML email template
        db_Asset_Models = Asset_Models.objects.select_related().order_by('model_category').filter(model_count_RTD__lt=F('model_min_qty')).values()

        context = {'asset_model': db_Asset_Models}
        return render(request, 'min_asset_levels/asset_report.html', context)
    else:
        response = redirect('/min_asset_levels/accounts/login/')
        return response
