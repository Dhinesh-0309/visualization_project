from django.db import models
from django.contrib.auth.models import User

class CSVUpload(models.Model):
    file = models.FileField(upload_to='uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"File uploaded at {self.uploaded_at}"

class UserMetrics(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    total_sales = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_purchases = models.IntegerField(default=0)
    top_product = models.CharField(max_length=255, blank=True, null=True)
    top_location = models.CharField(max_length=255, blank=True, null=True)
    highest_sales_month = models.IntegerField(default=0)

    def __str__(self):
        return f"Metrics for {self.user.username}"
