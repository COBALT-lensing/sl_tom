from django.core.management.base import BaseCommand

from tqdm import tqdm

from zooniverse.aggregation import PeakGrouperTargetAggregator
from zooniverse.models import ZooniverseTarget, ZooniverseTargetReduction


class Command(BaseCommand):
    help = "Aggregates all unaggregated targets"

    def handle(self, *args, **options):
        aggregated_targets = ZooniverseTargetReduction.objects.all().values_list(
            "target_id", flat=True
        )
        targets = ZooniverseTarget.objects.exclude(pk__in=aggregated_targets)
        for target in tqdm(targets, total=targets.count()):
            PeakGrouperTargetAggregator(target).save()
