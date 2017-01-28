from django.core.files.storage import Storage
from django.conf import settings
from hdfs import InsecureClient


class HDFSStorage(Storage):
    def __init__(self, option=None):
        if not option:
            option = settings.HDFS_STORAGE_OPTIONS
        host = option.get('HOST', 'default')
        port = option.get('PORT', 50070)
        user = option.get('USER', None)
        url = 'http://{0}:{1}'.format(host, port)
        self.client = InsecureClient(url=url, user=user)

    def _open(self, name, mode):
        with self.client.read(name) as reader:
            data = reader.read()
        return data

    def _save(self, name, content):
        self.client.write(hdfs_path=name, data=content)

    def listdir(self, path):
        return self.client.list(hdfs_path=path)

    def delete(self, name):
        self.client.delete(hdfs_path=name)

    def exists(self, name):
        return self.client.status(hdfs_path=name, strict=False) is not None

    def size(self, name):
        return self.client.status(hdfs_path=name).get('length')
