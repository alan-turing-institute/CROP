import logging
from pathlib import Path
import subprocess

import azure.functions as func


def main(mytimer: func.TimerRequest) -> None:
    # The order of these imports, that GESCalibrationV1 is run before pipelineV1_1 is
    # imported, actually matters.
    import GESCalibrationV1

    GESCalibrationV1.main()

    import pipelineV1_1

    pipelineV1_1.main()
