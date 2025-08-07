from astropy import units

from django.db import models

from lightkurve.io.tess import read_tess_lightcurve

from zooniverse.client import project


def fetch_tess_data(data_uri):
    ts = read_tess_lightcurve(data_uri)
    # Trim the first few hours from the start as loads of SPOC light curves seem to start with spurious peaks
    ts = ts[ts["time"] > ts["time"][0] + 3 * units.hour]
    return ts


class ZooniverseSurvey(models.Model):
    TESS = "TESS"
    FETCH_DATA_CHOICES = ((TESS, "TESS"),)
    FETCH_DATA_METHODS = {
        TESS: fetch_tess_data,
    }

    name = models.CharField(max_length=50)

    fetch_data_method = models.CharField(
        max_length=10, choices=FETCH_DATA_CHOICES, null=True, blank=True
    )

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def fetch_data(self, data_uri):
        if not self.fetch_data_method:
            return None
        return self.FETCH_DATA_METHODS[self.fetch_data_method](data_uri)


class ZooniverseTarget(models.Model):
    survey = models.ForeignKey(ZooniverseSurvey, on_delete=models.CASCADE)
    identifier = models.CharField(max_length=128)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.survey} {self.identifier}"

    def aggregated_annotations(self):
        tr = self.zooniversetargetreduction_set.order_by("-created").first()
        if tr is None:
            return None
        return tr.reduced_annotations

    def annotations(self):
        return self.classifications().values_list("annotation", flat=True)

    def classifications(self):
        return ZooniverseClassification.objects.filter(
            subject_id__in=self.zooniversesubject_set.all().values_list("pk", flat=True)
        )

    @property
    def data_url(self):
        return self.zooniversesubject_set.all().first().data_url

    def fetch_data(self):
        return self.survey.fetch_data(self.data_url)


class ZooniverseSubject(models.Model):
    subject_id = models.BigIntegerField(unique=True)
    target = models.ForeignKey(ZooniverseTarget, on_delete=models.CASCADE)

    sequence = models.CharField(max_length=50, help_text="Sector, data release, etc.")
    data_url = models.URLField(null=True, blank=True)
    start_time = models.DateTimeField(
        null=True, blank=True, help_text="Earliest time in the light curve"
    )
    end_time = models.DateTimeField(
        null=True, blank=True, help_text="Latest time in the light curve"
    )

    metadata = models.JSONField()

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def talk_url(self):
        return f"https://www.zooniverse.org/projects/{project.slug}/talk/subjects/{self.subject_id}"

    @property
    def annotations(self):
        return self.zooniverseclassification_set.values_list("annotation", flat=True)

    @property
    def annotation_count(self):
        return len(self.annotations)


class ZooniverseClassification(models.Model):
    classification_id = models.BigIntegerField(unique=True)
    subject = models.ForeignKey(ZooniverseSubject, on_delete=models.CASCADE)

    user_id = models.BigIntegerField(null=True, blank=True)
    timestamp = models.DateTimeField()
    annotation = models.JSONField()

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


class ZooniverseTargetReduction(models.Model):
    """
    Reduced classifications for targets.
    """

    target = models.ForeignKey(ZooniverseTarget, on_delete=models.CASCADE)
    classifications = models.ManyToManyField(ZooniverseClassification)

    reduced_annotations = models.JSONField()

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
