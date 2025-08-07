from collections import defaultdict
from functools import cached_property

import numpy

from astropy.time import Time

from zooniverse.models import ZooniverseTarget, ZooniverseTargetReduction


class TargetAggregator(object):
    """
    Base class for target aggregation. Project-specific logic should be implemented in a subclass.
    """

    MIN_ANNOTATIONS = 5

    def __init__(self, target):
        if type(target) is int:
            self.target = ZooniverseTarget.objects.get(target)
        else:
            self.target = target

    def aggregated_annotations(self):
        x_mins, x_mids, x_maxs, groups = (
            defaultdict(list),
            defaultdict(list),
            defaultdict(list),
            set(),
        )
        for annotation in self.annotations():
            x_min = annotation["x"] - annotation["width"]
            x_max = annotation["x"] + annotation["width"]
            try:
                group = self.group_between(x_min, x_max).jd
            except ValueError:
                continue
            groups.add(group)
            x_mids[group].append(annotation["x"])
            x_mins[group].append(x_min)
            x_maxs[group].append(x_max)
        aggregated_annotations = defaultdict(list)
        for group in groups:
            n_annotations = len(x_mids[group])
            if n_annotations < self.MIN_ANNOTATIONS:
                continue
            aggregated_annotations["x_min"].append(
                Time(numpy.median(x_mins[group]), format="jd").jd
            )
            aggregated_annotations["x_mid"].append(
                Time(numpy.median(x_mids[group]), format="jd").jd
            )
            aggregated_annotations["x_max"].append(
                Time(numpy.median(x_maxs[group]), format="jd").jd
            )
            aggregated_annotations["width"].append(
                aggregated_annotations["x_max"][-1]
                - aggregated_annotations["x_min"][-1]
            )
            aggregated_annotations["annotations"].append(n_annotations)
            aggregated_annotations["index"].append(group)
        return aggregated_annotations

    def annotations(self):
        for annotation in self.target.annotations():
            annotation = annotation[0]["value"]
            if len(annotation) == 0:
                continue
            yield annotation[0]

    def group_between(self, x_min, x_max):
        """
        Take a minimum and maximum time and return the canonical grouped time
        between them. How to do this will be project specific.
        """
        raise NotImplementedError

    def save(self):
        aggregated_annotations = self.aggregated_annotations()
        if aggregated_annotations is None:
            return None
        tr = ZooniverseTargetReduction.objects.create(
            target=self.target,
            reduced_annotations=aggregated_annotations,
        )
        tr.classifications.set(
            list(self.target.classifications().values_list("pk", flat=True))
        )

    @cached_property
    def target_data(self):
        return self.target.fetch_data()


class PeakGrouperTargetAggregator(TargetAggregator):
    """
    An aggregator that groups annotations according to the time of the largest peak
    contained in each annotation. Suitable for stellar pulsations, microlensing, etc.
    """

    def aggregated_annotations(self):
        if self.target_data is None:
            return None
        return super().aggregated_annotations()

    def data_between(self, start_time, end_time):
        return self.target_data[
            (self.target_data["time"] >= start_time)
            & (self.target_data["time"] <= end_time)
        ]

    def group_between(self, x_min, x_max):
        if type(x_min) is float:
            x_min = Time(x_min, format="jd")
        if type(x_max) is float:
            x_max = Time(x_max, format="jd")
        data = self.data_between(x_min, x_max)
        return data[numpy.argmax(data["flux"])]["time"]
