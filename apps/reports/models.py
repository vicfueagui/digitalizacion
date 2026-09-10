from django.db import models


class OperationalReport(models.Model):
    class Meta:
        managed = False
        default_permissions = ()
        permissions = [("view_operational_reports", "Puede consultar reportes operativos")]
