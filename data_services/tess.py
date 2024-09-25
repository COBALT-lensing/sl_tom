import datetime
import logging
import tempfile

from astropy import units
from astroquery.mast import Observations

from crispy_forms.layout import Div, HTML

from django import forms
from django.conf import settings
from django.core.files import File

from lightkurve.io.tess import read_tess_lightcurve

import numpy

import tom_dataproducts.single_target_data_service.single_target_data_service as stds
from tom_targets.models import Target
from tom_dataproducts.data_processor import run_data_processor, DataProcessor
from tom_dataproducts.exceptions import InvalidFileFormatException
from tom_dataproducts.models import DataProduct


logger = logging.getLogger(__name__)

DEFAULT_CONE_SEARCH_RADIUS = "1 arcsec"
DEFAULT_BIN_SIZE = 1 * units.day


# Flux to mag functions from https://github.com/tobin-wainer/elk/blob/ee90825bbbb88edf75413434a2e5d9e73cb09b2f/elk/utils.py#L33


def flux_to_mag(flux):
    """Converts flux to TESS Magnitudes

    Parameters
    ----------
    flux : :class:`~numpy.ndarray` or `float`
        flux in terms of e/s [for TESS]

    Returns
    -------
    mag : :class:`~numpy.ndarray` or `float`
        TESS Magnitude centered in the I band
    """
    m1 = 10  # calibration mag
    f1 = 15000  # Calibration Flux corresponding to the calibration mag
    mag = 2.5 * numpy.log10(f1 / flux) + m1
    return mag


def flux_err_to_mag_err(flux, flux_err):
    """Converts TESS Flux Errors to Magnitude errors

     Parameters
     ----------
     flux : class: `~numpy.ndarray` or `float`
         flux in terms of e/s [for TESS]
     flux_err : class: `~numpy.ndarray` or `float`
        flux error in terms of e/s [for TESS]

     Returns
     -------
    mag_err : class: `~numpy.ndarray` or `float`
         TESS Magnittude errors
    """
    d_mag_d_flux = -2.5 / (flux * numpy.log(10))
    m_err_squared = abs(d_mag_d_flux) ** 2 * flux_err**2
    return numpy.sqrt(m_err_squared)


class TessProcessor(DataProcessor):
    def data_type_override(self):
        return "photometry"

    def process_data(self, data_product):
        """
        Reads a TESS light curve with lightkurve and returns photometry as tuples.
        """

        ts = read_tess_lightcurve(data_product.data.path)
        ts = ts[~ts["flux"].mask & ~ts["flux_err"].mask]
        ts = ts.bin(time_bin_size=DEFAULT_BIN_SIZE)
        ts = ts[~numpy.isnan(ts["flux"]) & ~numpy.isnan(ts["flux_err"])]
        return [
            (
                row["time"].utc.to_datetime(timezone=datetime.timezone.utc),
                {
                    "flux": float(row["flux"].value),
                    "flux_err": float(row["flux_err"].value),
                    "magnitude": float(flux_to_mag(row["flux"].value)),
                    "error": float(
                        flux_err_to_mag_err(row["flux"].value, row["flux_err"].value)
                    ),
                    "telescope": "TESS",
                    "filter": "TESS",
                },
                "TESS",
            )
            for row in ts
        ]


class TessSingleTargetDataServiceQueryForm(stds.BaseSingleTargetDataServiceQueryForm):

    sequence_number = forms.CharField(
        label="Sectors (comma separated):",
        required=False,
    )

    def layout(self):
        return Div(
            Div(
                Div("sequence_number", css_class="col-md-2"),
                css_class="row",
            ),
            Div(
                HTML(
                    f"<p>Default cone search radius of {DEFAULT_CONE_SEARCH_RADIUS} in use.</p>"
                )
            ),
            HTML("<hr>"),
        )

    def clean(self):
        """
        After cleaning the form data field-by-field, do any necessary cross-field validation.
        """
        cleaned_data = super().clean()
        logger.debug(
            f"TessSingleTargetDataServiceQueryForm.clean() -- cleaned_data: {cleaned_data}"
        )

        sequence_numbers_ints = []
        for n in [s.strip() for s in cleaned_data["sequence_number"].split(",")]:
            if len(n) == 0:
                continue
            if not n.isdigit():
                raise forms.ValidationError("Sectors must be integers")
            sequence_numbers_ints.append(int(n))
        cleaned_data["sequence_number"] = sequence_numbers_ints

        return cleaned_data


class TessSingleTargetDataService(stds.BaseSingleTargetDataService):
    name = "TESS"
    info_url = "https://archive.stsci.edu/missions-and-data/tess"
    data_service_type = "Catalog Search"

    def __init__(self):
        super().__init__()
        self.success_message = "TESS success message"

    def get_form(self):
        return TessSingleTargetDataServiceQueryForm

    def query_service(self, query_parameters):
        logger.debug(f"Querying TESS service with params: {query_parameters}")

        target = Target.objects.get(pk=query_parameters.get("target_id"))
        if not Target.objects.filter(pk=query_parameters.get("target_id")).exists():
            raise stds.SingleTargetDataServiceException(
                f"Target {query_parameters.get('target_id')} does not exist"
            )

        provenance_name = settings.SINGLE_TARGET_DATA_SERVICES["TESS"].get(
            "provenance_name", "TESS-SPOC"
        )
        query_results = Observations.query_criteria(
            coordinates=f"{target.ra} {target.dec}",
            provenance_name=provenance_name,
            radius=DEFAULT_CONE_SEARCH_RADIUS,
            sequence_number=query_parameters.get("sequence_number", []),
        )

        data_products_count = 0

        for result in query_results:
            data_product_name = f"tess-{provenance_name}-{result['target_name']}-{result['sequence_number']}"
            dp, created = DataProduct.objects.get_or_create(
                product_id=data_product_name,
                target=target,
                data_product_type=self.get_data_product_type(),
            )

            if created:
                with tempfile.NamedTemporaryFile() as fp:
                    Observations.download_file(
                        result["dataURL"],
                        local_path=fp.name,
                        cache=False,
                    ),
                    dp.data = File(fp, name=f"{data_product_name}.fits")
                    dp.save()
                    logger.info(
                        f"Created dataproduct {data_product_name} from TESS (MAST) query"
                    )
            else:
                logger.warning(
                    f"DataProduct {data_product_name} already exists, skipping download"
                )

            try:
                run_data_processor(dp)
            except InvalidFileFormatException as e:
                error_msg = (
                    f"Error while processing {data_product_name} (the returned TESS data) "
                    f"into ReducedDatums: {repr(e)}"
                )
                logger.error(error_msg)
                continue
            data_products_count += 1

        self.success_message = (
            f"Successfully created or updated {data_products_count} TESS data products"
        )

        return True

    def validate_form(self, query_parameters):
        """
        Same thing as query_service, but a dry run. You can
        skip this in different modules by just using "pass"

        Typically called by the .is_valid() method.
        """
        logger.info(f"Validating PaTESSnSTARRS service with params: {query_parameters}")

    def get_success_message(self):
        return self.success_message

    def get_data_product_type(self):
        return "tess_photometry"
