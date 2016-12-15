from django.test import TestCase
from features.tests.factories import FeatureFactory


class TestFeatureModel(TestCase):
    def test_select_as_target(self):
        feature1 = FeatureFactory()
        feature1.select_as_target()
        feature1.save()

        self.assertTrue(feature1.is_target)

        feature2 = FeatureFactory()
        feature2.select_as_target()
        feature2.save()
        feature1.refresh_from_db()

        self.assertTrue(feature2.is_target)
        self.assertFalse(feature1.is_target)
