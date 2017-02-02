from django.test import TestCase
from features.tests.factories import DatasetFactory
import os
from features.models import Dataset


class TestDatasetModel(TestCase):
    def test_delete_file_on_delete(self):
        dataset = DatasetFactory()

        file_path = dataset.content.path

        self.assertTrue(os.path.isfile(file_path))
        Dataset.objects.all().delete()
        self.assertFalse(os.path.isfile(file_path))
