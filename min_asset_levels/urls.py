from django.urls import path
from django.conf.urls.static import static

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('asset_models/editminqty', views.minQtyUpdate, name='editminqty'),
    path('asset_models/editminqty/<int:pk>', views.minQtyUpdate, name='editminqty'),
    path('asset_models/data.json', views.assetModelData, name='asset_model_json'),
    path('asset_models/assetreport', views.html_asset_report, name='html_asset_report'),
]