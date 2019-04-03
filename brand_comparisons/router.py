from rest_framework import routers

from brand_comparisons.views import BrandComparisonViewSet, \
    BrandComparisonSegmentViewSet, BrandComparisonSegmentRowViewSet

router = routers.SimpleRouter()
router.register(r'brand_comparisons', BrandComparisonViewSet)
router.register(r'brand_comparison_segments', BrandComparisonSegmentViewSet)
router.register(r'brand_comparison_segment_rows',
                BrandComparisonSegmentRowViewSet)
