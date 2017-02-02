from django.test import TestCase
from features.storages import HDFSStorage
from unittest.mock import patch


class TestHDFSStorage(TestCase):
    FILENAME = 'example.json'

    def setUp(self):
        self.client = HDFSStorage()

    @patch('features.storage.InsecureClient.write')
    def test_open(self, write_mock):
        content = '{"a_key":"a_value"}'
        self.client.save(self.FILENAME, content)
        write_mock.assert_called_once_with(hdfs_path=self.FILENAME, data=content)
