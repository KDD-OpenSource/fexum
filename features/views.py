from rest_framework.views import APIView
from features.models import Feature
from features.serializers import FeatureSerializer
from rest_framework.response import Response


class FeatureListView(APIView):
    def get(self, *args, **kwargs):
        features = Feature.objects.all()
        serializer = FeatureSerializer(instance=features, many=True)
        return Response(serializer.data)


class SelectTargetView(APIView):
    pass


class FeatureSamplesView(APIView):
    pass


class FeatureHistogramView(APIView):
    pass


class FeatureSlicesView(APIView):
    pass
