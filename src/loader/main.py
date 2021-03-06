# RUNNING EVERY 6 HOURS
import pandas as pd
import requests
from copy import deepcopy
import os
import yaml
from datetime import datetime
import numpy as np
import importlib

# Environment variables from '../.env' file
from dotenv import load_dotenv
from pathlib import Path

env_path = Path("..") / ".env"
load_dotenv(dotenv_path=env_path, override=True)

from logger import logger
from utils import (
    get_last,
    get_config,
    build_file_path,
    get_endpoints,
)

from notifiers import get_notifier

import ssl

ssl._create_default_https_context = ssl._create_unverified_context


def _write_data(data, endpoint):

    output_path = build_file_path(endpoint)

    data["data_last_refreshed"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data.to_csv(output_path, index=False)

    logger.info(
        "WRITTING DATA FOR {}",
        " - ".join([endpoint["python_file"], str(data["data_last_refreshed"].max())]),
    )


def _test_data(data, tests, endpoint):

    results = [v(data) for k, v in tests.items()]

    if not all(results):

        logger.info("TESTS FAILED FOR {}", endpoint["python_file"])

        for k, v in tests.items():
            if not v(data):

                logger.error(
                    "TEST FAILED FOR ENDPOINT {}: {}", endpoint["python_file"], k
                )

        return False

    else:
        logger.info("TESTS PASSED FOR {}", endpoint["python_file"])

        return True


@logger.catch
def main(endpoint):

    logger.info("STARTING: {}", endpoint["python_file"])

    try:
        runner = importlib.import_module("endpoints.{}".format(endpoint["python_file"]))

        data = runner.now(get_config(), force=True)
        data = data.reindex(sorted(data.columns), axis=1)

        if _test_data(data, runner.TESTS, endpoint):

            _write_data(data, endpoint)

    except Exception as e:
        logger.opt(exception=True).error("ERROR: {}", e)
        return e

    return None


if __name__ == "__main__":
    hasError = False

    for endpoint in get_endpoints():

        if endpoint.get("skip"):
            continue

        err = main(endpoint)

        if err is not None:
            hasError = True

    if hasError:
        exit(1)
