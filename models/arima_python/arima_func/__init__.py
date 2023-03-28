import logging
from pathlib import Path
import subprocess

import azure.functions as func

from run_pipeline import run_pipeline


def main(mytimer: func.TimerRequest) -> None:
    run_pipeline()
