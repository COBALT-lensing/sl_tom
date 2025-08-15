from astropy import units

from django.core.files.base import ContentFile
from django.db import models

from lightkurve.io.tess import read_tess_lightcurve

from matplotlib import pyplot

from zooniverse.client import project
from zooniverse.lightcurve import generate_image
from django.urls import reverse


def fetch_tess_data(data_uri):
    try:
        ts = read_tess_lightcurve(data_uri)
    except (FileNotFoundError, ValueError, TypeError):
        return None
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


def zooniversetarget_lightcurve_image_path(instance, filename):
    return f"target_lightcurves/{str(instance.pk)[:3]}/{instance.pk}/{filename}"


class ZooniverseTarget(models.Model):
    survey = models.ForeignKey(ZooniverseSurvey, on_delete=models.CASCADE)
    identifier = models.CharField(max_length=128)

    generated_lightcurve_image = models.ImageField(
        null=True, upload_to=zooniversetarget_lightcurve_image_path
    )

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

    def generate_lightcurve_image(self):
        annotations = self.aggregated_annotations()
        if annotations and len(annotations) > 0:
            highlights = list(
                zip(annotations["x_min"], annotations["x_mid"], annotations["x_max"])
            )
        else:
            highlights = None
        data = self.fetch_data()
        if data is None:
            return
        fig = generate_image(
            data,
            highlights=highlights,
        )
        image_data = ContentFile(b"")
        try:
            fig.savefig(image_data)
        except:
            pass
        else:
            self.generated_lightcurve_image.save(
                "lightcurve.png", image_data, save=True
            )
        finally:
            pyplot.close(fig=fig)

    def get_absolute_url(self):
        return reverse("zooniverse:zooniverse_target_detail", args=[str(self.pk)])

    @property
    def lightcurve_image(self):
        if not self.generated_lightcurve_image:
            self.generate_lightcurve_image()
        if self.generated_lightcurve_image:
            return self.generated_lightcurve_image
        return None


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
