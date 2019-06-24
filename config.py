# -*- coding: utf-8 -*-
import os

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

class Config:
    secret_key = os.environ.get("SECRET_KEY")
    team_info = os.environ.get("TEAM_INFO_JSON")
    service_provider = os.environ.get("SERVICE_PROVIDER")
    tinydb_document = os.environ.get("TINYDB_DOCUMENT")

    background_color = [
        'rgba(255, 99, 132, 0.2)',
        'rgba(54, 162, 235, 0.2)',
        'rgba(255, 206, 86, 0.2)',
        'rgba(75, 192, 192, 0.2)',
        'rgba(153, 102, 255, 0.2)',
        'rgba(255, 159, 64, 0.2)'
    ]

    border_color = [
        'rgba(255,99,132,1)',
        'rgba(54, 162, 235, 1)',
        'rgba(255, 206, 86, 1)',
        'rgba(75, 192, 192, 1)',
        'rgba(153, 102, 255, 1)',
        'rgba(255, 159, 64, 1)'
    ]

    opeg_commit = int(os.environ.get("OPEG_COMMIT"))
    opeg_issue = int(os.environ.get("OPEG_ISSUE"))
    opeg_pr = int(os.environ.get("OPEG_PR"))
    opeg_license = int(os.environ.get("OPEG_LICENSE"))
    opeg_contributor = int(os.environ.get("OPEG_CONTRIBUTOR"))
    opeg_branch = int(os.environ.get("OPEG_BRANCH"))
