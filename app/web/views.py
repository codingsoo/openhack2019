from flask import render_template, redirect
from config import Config
from app.db import Database
from datetime import datetime
from dateutil.parser import parse

from . import web

@web.route("/", methods=['GET'])
def home():
    """현재 팀들에 대한 점수와 순위를 열람할 수 있는 페이지."""
    return render_template('dashboard.html',
            description=Config.service_provider,
            team_list=Database.get_all(),
            chart_data=Database.get_chart_data())

@web.route("/detail/<name>", methods=['GET'])
def detail(name):
    """팀당 소속 Repo, 팀원을 편집하거나 즉시 크롤링을 실행시킬 수 있는 관리 페이지."""
    team = Database.get_info(name)

    if len(team) == 0:
        return redirect("/")

    #team_update = datetime.strptime(team["timestamp"], '%Y-%m-%dT%H:%M:%S %Z%z')
    team_update = parse(team["timestamp"])
    team["g_timestamp"] = team_update.strftime("%Y년 %m월 %d일 %H시 %M분 %S초")

    for repo in team["repos"]:
        repo["g_license"] = "없음" \
            if repo["license"] == "Unavailable" \
            else repo["license"]
        
        language = str()
        for lang in repo["languages"]:
            language += lang["name"] + " (" + lang["percent"] + "%), "
        repo["g_languages"] = language[:-2]

        repo["g_issues"] = int(repo["issue_open"]) + int(repo["issue_closed"])
        repo["g_pr"] = int(repo["pr_open"]) + int(repo["pr_closed"])

        branches = str()
        for branch in repo["alive_branches"]:
            branches += branch + ", "
        repo["g_alive_branches"] = branches[:-2]

        contributors = str()
        for person in repo["contributors"]:
            contributors += person["name"] + " (" + str(person["count"]) + "개), "
        repo["g_contributors"] = contributors[:-2]

        issuers = str()
        for issuer in repo["issuers"].keys():
            issuers += issuer + " (" + str(repo["issuers"][issuer]) + "개), "
        repo["g_issuers"] = issuers[:-2]
    
    return render_template('detail.html',
        description=Config.service_provider,
        team=team,
        team_list=Database.get_all(),
        cph_criteria=Config.opeg_commit)

