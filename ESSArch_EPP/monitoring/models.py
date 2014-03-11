from datetime import timedelta
from django.db import models
from django.utils import timezone

class Log(models.Model):
    level = models.CharField(max_length=10)
    msg = models.TextField()
    datetime = models.DateTimeField(auto_now_add=True, blank=True)

    class Meta:
        ordering = ['-datetime']

    def recent(self):
        now = timezone.now()
        RECENT = timedelta(days=1)
        recent = self.datetime > (now - RECENT) 
        return recent

class MonitoringObject(models.Model):     
    key = models.CharField(max_length=255)
    alarm = models.IntegerField(default=0)
    alarm_num = models.IntegerField(default=0)
    alarm_sub = models.TextField(blank=True)
    alarm_msg = models.TextField(blank=True)
    checked = models.DateTimeField(default='2014-01-01 00:01')
    
    class Meta:
        permissions = (                    
            ("list_monitoringobject", "Can list monitoringobject"),
        )
        #verbose_name = 'Alarm'
