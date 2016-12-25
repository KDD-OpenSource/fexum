from django.test import TestCase
from features.tests.factories import FeatureFactory, TargetFactory
from features.models import Target


class TestTargetModel(TestCase):
    def test_select_target(self):
        target = TargetFactory()
        self.assertEqual(Target.objects.count(), 1)
        self.assertEqual(Target.objects.get(), target)

        # The creation of a new target replaces the old one
        target2 = TargetFactory()
        self.assertEqual(Target.objects.count(), 1)
        self.assertEqual(Target.objects.get(), target2)
