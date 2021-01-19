from django.db import models

class Asset_Models(models.Model):
    snipe_model_id = models.IntegerField()
    model_name = models.CharField(max_length=250)
    model_manufacturer_name = models.CharField(max_length=250)
    model_number = models.CharField(max_length=250)
    model_category = models.CharField(max_length=250)
    model_count = models.IntegerField()
    model_deleted = models.BooleanField(default=False)
    model_min_qty = models.PositiveIntegerField("minimum quantity", null=True)

class Asset_Report(models.Model):
    snipe_model_id = models.IntegerField()
    model_name = models.CharField(max_length=250)
    model_manufacturer_name = models.CharField(max_length=250)
    model_number = models.CharField(max_length=250)
    model_category = models.CharField(max_length=250)
    model_location = models.CharField(max_length=250)
    model_custom_fields = models.TextField()