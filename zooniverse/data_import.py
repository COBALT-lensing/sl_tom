import json
import logging
import requests
import time

from dateutil.parser import parse as date_parse

from tqdm import tqdm

from zooniverse.client import project, workflow
from zooniverse.models import (
    ZooniverseClassification,
    ZooniverseSubject,
    ZooniverseTarget,
    ZooniverseSurvey,
)

logger = logging.getLogger(__name__)


def generate_subject_export(wait=False):
    project.generate_export("subjects")
    if wait:
        project.wait_export("subjects")


def generate_classification_export(wait=False):
    workflow.generate_export("classifications")
    if wait:
        workflow.wait_export("classifications")


def get_subject_export():
    return project.get_export("subjects").csv_dictreader()


def get_classification_export():
    return workflow.get_export("classifications").csv_dictreader()


def import_classifications(limit=None, warn_missing_subjects=False):
    """
    Downloads the latest workflow classifications export and creates new ZooniverseClassification
    objects based on it.
    """
    BATCH_SIZE = 1e5

    total = 0
    i = 0
    with tqdm(total=limit) as pbar:
        new_classifications = []
        for attempt in range(5):
            existing_classifications = list(
                ZooniverseClassification.objects.all().values_list(
                    "classification_id", flat=True
                )
            )
            existing_subjects = dict(
                ZooniverseSubject.objects.all().values_list("subject_id", "pk")
            )
            try:
                for c in get_classification_export():
                    if limit is not None and total + len(new_classifications) >= limit:
                        break
                    classification_id = int(c["classification_id"])
                    subject_id = int(c["subject_ids"])
                    user_id = c["user_id"]
                    if len(user_id) == 0:
                        user_id = None
                    else:
                        user_id = int(user_id)

                    if classification_id in existing_classifications:
                        existing_classifications.remove(classification_id)
                        continue

                    if subject_id not in existing_subjects:
                        if warn_missing_subjects:
                            logger.warning(
                                f"Skipping classification {classification_id} for unknown subject {subject_id}"
                            )
                        continue

                    annotation = json.loads(c["annotations"])
                    timestamp = date_parse(c["created_at"])

                    new_classifications.append(
                        ZooniverseClassification(
                            classification_id=classification_id,
                            subject_id=existing_subjects[subject_id],
                            user_id=user_id,
                            timestamp=timestamp,
                            annotation=annotation,
                        )
                    )
                    pbar.update(1)
                    i += 1
                    if i >= BATCH_SIZE:
                        total += len(
                            ZooniverseClassification.objects.bulk_create(
                                new_classifications
                            )
                        )
                        new_classifications = []
                        i = 0
            except requests.RequestException:
                time.sleep(attempt * 60)
                continue
            break
    total += len(ZooniverseClassification.objects.bulk_create(new_classifications))
    return total


def import_subjects(
    target_identifier=None,
    survey=None,
    survey_identifier=None,
    sequence=None,
    sequence_identifier=None,
    limit=None,
):
    """
    Downloads the latest subjects export and creates new ZooniverseSubject objects.

    Options:
        - target_identifier: The metadata key name which gives the target/object ID.
          Any subjects which don't have this metadata key will be skipped.
        - survey: If this and survey_identifier are both provided, filters subjects
          to just the ones in the specified survey. If survey_identifier is not provided,
          assumes all subjects are in the specified survey.
        - survey_identifier: The metadata key name which gives the survey name.
        - sequence: If this and sequence_identifier are both provided, filters subjects
          to just the ones in the specified sequence. Has no effect if sequence_identifier
          is not provided.
        - sequence_identifier: the metadata key name which gives the sequence name (i.e.
          the data release number, sector name, or other grouping).
    """
    if survey is not None:
        survey = ZooniverseSurvey.objects.get_or_create(name=survey)[0]

    existing_subjects = ZooniverseSubject.objects.all()
    if survey is not None:
        existing_subjects = existing_subjects.filter(target__survey=survey)
    existing_subjects = existing_subjects.values_list("subject_id", flat=True)

    count = 0
    for s in tqdm(get_subject_export(), total=limit):
        if limit is not None and count > limit:
            break
        subject_id = int(s["subject_id"])

        if subject_id in existing_subjects:
            continue

        locations = json.loads(s["locations"])
        metadata = json.loads(s["metadata"])

        if survey_identifier is not None:
            survey_name = metadata.get(survey_identifier, None)
            if survey_name is None:
                continue
            if survey is None:
                survey = ZooniverseSurvey.objects.get_or_create(name=survey_name)[0]
            else:
                if survey.name != survey_name:
                    continue

        target = None
        if target_identifier is not None:
            target_name = metadata.get(target_identifier, None)
            if target_name is None:
                continue
            target = ZooniverseTarget.objects.get_or_create(
                survey=survey, identifier=target_name
            )[0]

        sequence_name = None
        if sequence_identifier is not None:
            sequence_name = metadata.get(sequence_identifier, None)
            if sequence_name is None:
                continue
            if sequence is not None and sequence != sequence_name:
                continue

        ZooniverseSubject.objects.create(
            subject_id=subject_id,
            metadata=s["metadata"],
            data_url=locations["0"],
            target=target,
            sequence=sequence_name,
        )
        count += 1
    return count
