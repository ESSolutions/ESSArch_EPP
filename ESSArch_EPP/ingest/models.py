from django.db import models
from django.core.urlresolvers import reverse


#class Notes(models.Model):
#    title   = models.CharField(max_length=255,help_text='Ange en title')
#    FRESHMAN = 'FR'
#    SOPHOMORE = 'SO'
#    JUNIOR = 'JR'
#    SENIOR = 'SR'
#    YEAR_IN_SCHOOL_CHOICES = (
#        (FRESHMAN, 'Freshman'),
#        (SOPHOMORE, 'Sophomore'),
#        (JUNIOR, 'Junior'),
#        (SENIOR, 'Senior'),
#    )
#    content = models.CharField(max_length=2,help_text='Ange typ av content',choices=YEAR_IN_SCHOOL_CHOICES,default=FRESHMAN)
#    content2 = models.TextField(default='hej1232',help_text='help content2 xxxxyyytest123')
#    added_at = models.DateTimeField(auto_now_add=True) 
#    last_update = models.DateTimeField(auto_now=True)
#    last_update2 = models.DateTimeField(auto_now=True)
#
#    def get_absolute_url(self):
#        return reverse('notes_list')

#class permission(models.Model):
#    class Meta:
#        permissions = (
#            ("list", "list"),
#            ("create", "create"),
#            ("update", "update"),
#            ("delete", "delete"),
#        )
