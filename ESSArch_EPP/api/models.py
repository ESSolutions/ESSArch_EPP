import os
import time
import hashlib
import uuid
from django.db import models
from django.core.files.uploadedfile import UploadedFile
from django.core.files.storage import FileSystemStorage
from django.utils import timezone
from django.conf import settings
from chunked_upload.models import CHUNKED_UPLOAD_CHOICES, UPLOADING, \
                AUTH_USER_MODEL, EXPIRATION_DELTA

def generate_upload_id():
    return uuid.uuid4().hex

class BaseChunkedUpload(models.Model):
    """
    Base chunked upload model. This model is abstract (doesn't create a table
    in the database).
    Inherit from this model to implement your own.
    """

    upload_id = models.CharField(max_length=32, unique=True, editable=False,
                                 default=generate_upload_id)
    # The field "file" need to be defined in your own class to set attributes.
    #file = models.FileField(max_length=255, upload_to=generate_filename,
    #                        storage=STORAGE)
    filename = models.CharField(max_length=255)
    offset = models.BigIntegerField(default=0)
    created_on = models.DateTimeField(auto_now_add=True)
    status = models.PositiveSmallIntegerField(choices=CHUNKED_UPLOAD_CHOICES,
                                              default=UPLOADING)
    completed_on = models.DateTimeField(null=True, blank=True)

    @property
    def expires_on(self):
        return self.created_on + EXPIRATION_DELTA

    @property
    def expired(self):
        return self.expires_on <= timezone.now()

    @property
    def md5(self):
        if getattr(self, '_md5', None) is None:
            md5 = hashlib.md5()
            for chunk in self.file.chunks():
                md5.update(chunk)
            self._md5 = md5.hexdigest()
        return self._md5

    def delete(self, delete_file=True, *args, **kwargs):
        storage, path = self.file.storage, self.file.path
        super(BaseChunkedUpload, self).delete(*args, **kwargs)
        if delete_file:
            storage.delete(path)

    def __unicode__(self):
        return u'<%s - upload_id: %s - bytes: %s - status: %s>' % (
            self.filename, self.upload_id, self.offset, self.status)

    def close_file(self):
        """
        Bug in django 1.4: FieldFile `close` method is not reaching all the
        way to the actual python file.
        Fix: we had to loop all inner files and close them manually.
        """
        file_ = self.file
        while file_ is not None:
            file_.close()
            file_ = getattr(file_, 'file', None)

    def append_chunk(self, chunk, chunk_size=None, save=True):
        self.close_file()
        self.file.open(mode='ab')  # mode = append+binary
        # We can use .read() safely because chunk is already in memory
        self.file.write(chunk.read())
        if chunk_size is not None:
            self.offset += chunk_size
        elif hasattr(chunk, 'size'):
            self.offset += chunk.size
        else:
            self.offset = self.file.size
        self._md5 = None  # Clear cached md5
        if save:
            self.save()
        self.close_file()  # Flush

    def get_uploaded_file(self):
        self.close_file()
        self.file.open(mode='rb')  # mode = read+binary
        return UploadedFile(file=self.file, name=self.filename,
                            size=self.offset)

    class Meta:
        abstract = True

from django.db import ProgrammingError
from configuration.models import Path

# TmpWorkareaUpload
try:
    TmpWorkarea_upload_root =  Path.objects.get(entity='TmpWorkarea_upload_path').value
except (Path.DoesNotExist, ProgrammingError) as e:
    TmpWorkarea_upload_root = settings.MEDIA_ROOT

def TmpWorkarea_filename(instance, filename):
    upload_path = os.path.join(TmpWorkarea_upload_root,'chunked_uploads/%Y/%m/%d')
    filename = os.path.join(upload_path, instance.upload_id + '.part')
    return time.strftime(filename)

class TmpWorkarea_storage(FileSystemStorage):
    def __init__(self):
        super(TmpWorkarea_storage, self).__init__(location=TmpWorkarea_upload_root)

class TmpWorkareaUpload(BaseChunkedUpload):
    file = models.FileField(max_length=255, upload_to=TmpWorkarea_filename,
                            storage=TmpWorkarea_storage())
    user = models.ForeignKey(AUTH_USER_MODEL, related_name='chunked_uploads', blank=True)

# GateareUpload
try:
    Gatearea_upload_root =  Path.objects.get(entity='path_gate').value
except (Path.DoesNotExist, ProgrammingError) as e:
    Gatearea_upload_root = settings.MEDIA_ROOT

def Gatearea_filename(instance, filename):
    upload_path = os.path.join(Gatearea_upload_root,'chunked_uploads/%Y/%m/%d')
    filename = os.path.join(upload_path, instance.upload_id + '.part')
    return time.strftime(filename)

class Gatearea_storage(FileSystemStorage):
    def __init__(self):
        super(Gatearea_storage, self).__init__(location=Gatearea_upload_root)

class GateareaUpload(BaseChunkedUpload):
    file = models.FileField(max_length=255, upload_to=Gatearea_filename,
                            storage=Gatearea_storage())
    user = models.ForeignKey(AUTH_USER_MODEL, blank=True)

# Override the default ChunkedUpload to make the `user` field nullable
#TmpWorkareaUpload._meta.get_field('user').null = True
#TmpWorkareaUpload._meta.get_field('file').upload_to = generate_filename2


