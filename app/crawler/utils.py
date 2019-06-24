from bs4 import BeautifulSoup
import requests
import json
import sys
import time
from pytz import timezone
from datetime import datetime
from config import Config
from app.db import Database

class Analyser:
    @classmethod
    def analyse(cls, team_info):
        repo_list = list()
        for item in team_info:
            repo_list += item["repos"]
        url_array = cls.process_url(repo_list)
        processed_array = list()
        for repo, code in zip(url_array, repo_list):
            try: 
                processed_array.append(
                    cls.crawl(repo, code, Config.opeg_commit)
                )
            except:
                print(sys.exc_info()[0], sys.exc_info()[1])
                try: 
                    processed_array.append(
                        cls.crawl(repo, code, Config.opeg_commit)    
                    )
                except:
                    print(sys.exc_info()[0], sys.exc_info()[1])
                    # 두 번 실패했으므로 스킵함
                    continue

        print(json.dumps(processed_array, indent=4))

        opeg_array = cls.evaluate(processed_array, team_info)

        # DB Transaction
        for team in opeg_array:
            Database.set_info(team)

        return opeg_array

    @classmethod
    def crawl(cls, repo, code, opeg_commit):
        """
        주어진 1개의 Repository에 대하여 크롤링을 시도합니다.
        @return ret 정보가 담긴 Dictionary 객체
        """
        ret = dict()
        ret["name"] = code
        ret["url"] = repo
        print("[+] Starting " + code)

        # Commits, Branch, License 고시 여부, 언어 사용 비율 추출
        print("[+] Getting fundamental information...")
        soup = BeautifulSoup(requests.get(repo).text, "html.parser")
        soup_normal_nums = soup.select("span.num.text-emphasized")
        ret["commits"] = int(soup_normal_nums[0].string.replace(",", "").strip())
        ret["alive_branch_count"] = int(soup_normal_nums[1].string.replace(",", "").strip())

        if len(soup.select(".octicon-law")) > 0:
            ret["license"] = soup.select(".octicon-law")[0].next_element.next_element.string.replace(",", "").strip()
        else:
            ret["license"] = "Unavailable"

        ret["languages"] = list()
        for lang, percent in zip(soup.select(".lang"), soup.select(".percent")):
            temp_dic = dict()
            temp_dic["name"], temp_dic["percent"] = lang.string, percent.string[0:-1]
            ret["languages"].append(temp_dic)

        ret["alive_branches"] = list()
        for branch in soup.select(".select-menu-item-text.css-truncate-target.js-select-menu-filter-text"):
            ret["alive_branches"].append(branch.string.strip())

        # 열고 닫힌 Issue의 갯수 추출
        print("[+] Getting issues...")
        soup = BeautifulSoup(requests.get(repo + "/issues").text, "html.parser")
        if len(soup.select(".states")) == 0:
            ret["issue_open"], ret["issue_closed"] = 0, 0
        else:
            issues = soup.select(".states")[0].text.strip().replace("Open", "").replace("Closed", "").replace(",", "").split()
            ret["issue_open"], ret["issue_closed"] = issues[0], issues[1]

        # 각 기여자별 Issue 갯수 추출
        issue_url = "/" + code + "/issues?utf8=%E2%9C%93&q=is%3Aissue"
        ret["issuers"] = dict()
        page = 0
        while issue_url is not None:
            page += 1
            print("[+] Issue: Page " + str(page) + " crawling...")
            soup = BeautifulSoup(requests.get("https://github.com" + issue_url).text, "html.parser")
            for i in soup.select("ul.js-active-navigation-container li"):
                issuer_name = i.select(".opened-by .muted-link")[0].get_text()
                if issuer_name in ret["issuers"]:
                    ret["issuers"][issuer_name] += 1
                else:
                    ret["issuers"][issuer_name] = 1

            next_page = soup.select(".next_page")
            if len(next_page) == 0:
                break
            
            issue_url = next_page[0].get("href")

        # 열고 닫힌 Pull Requests의 갯수 추출
        print("[+] Getting pull requests...")
        soup = BeautifulSoup(requests.get(repo + "/pulls").text, "html.parser")
        if len(soup.select(".states")) == 0:
            ret["pr_open"], ret["pr_closed"] = 0, 0
        else:
            pulls = soup.select(".states")[0].text.strip().replace("Open", "").replace("Closed", "").replace(",", "").split()
            ret["pr_open"], ret["pr_closed"] = pulls[0], pulls[1]

        # 기여자 추출
        print("[+] Getting contributors...")
        payload = {
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36"
        }
        ret["contributors"] = list()
        ret["contributor_count"] = 0
        contributors = requests.get(repo + "/graphs/contributors-data", headers=payload).json()
        if "unusable" not in contributors:
            for person in contributors:
                temp_dic = dict()
                temp_dic["name"] = person["author"]["login"]
                temp_dic["avatar"] = person["author"]["avatar"][0:-2] + "360"
                temp_dic["count"] = person["total"]
                ret["contributors"].append(temp_dic)
                ret["contributor_count"] += 1

        # Recent commits (최고 20개, 최저 0개), 기간별 나누기 연산
        print("[+] Getting CPH...")
        soup = BeautifulSoup(requests.get(repo + "/commits/master.atom").text, "html.parser")

        ret["cph"] = cls.get_cph(soup, opeg_commit)
        
        # Github의 Abuse Detection을 회피하기 위한 3초 Sleep
        print("[+] Avoiding GitHub abuse detection...")
        time.sleep(3)
        return ret

    @classmethod
    def evaluate(cls, crawlhub, team_info):
        """
        주어진 팀 정보와 해석된 Repo 정보를 바탕으로 OPEG 점수를 계산합니다.
        @return ret 각 팀의 점수가 담긴 Dictionary 리스트
        """
        ret = list()
        for team in team_info:
            rep_result = {
                "name": team["name"],
                "timestamp": datetime.now(timezone("Asia/Seoul")).isoformat(),
                "repos": list(),
                "commit": 0,
                "cph": 0,
                "issue": 0,
                "license": 0,
                "pr": 0,
                "contributor": 0,
                "branch": 0
            }
            for repo in crawlhub:
                if team["repos"].count(repo["name"]) == 1:
                    rep_result["repos"].append(repo.copy())
                    rep_result["commit"] += int(repo["commits"])
                    if repo["license"] != "Unavailable":
                        rep_result["license"] = 1
                    rep_result["issue"] += int(repo["issue_open"])
                    rep_result["issue"] += int(repo["issue_closed"])
                    rep_result["contributor"] += int(repo["contributor_count"])
                    rep_result["branch"] += int(repo["alive_branch_count"])
                    rep_result["pr"] += int(repo["pr_open"])
                    rep_result["pr"] += int(repo["pr_closed"])
                    rep_result["cph"] += int(repo["cph"])
            rep_result["score"] = cls.get_opeg({
                "commit": rep_result["commit"],
                "cph": rep_result["cph"],
                "issue": rep_result["issue"],
                "license": rep_result["license"],
                "pr": rep_result["pr"],
                "contributor": rep_result["contributor"],
                "branch": rep_result["branch"]
            })
            ret.append(rep_result.copy())
        
        return ret

    @classmethod
    def get_opeg(cls, score):
        """
        주어진 팀별 점수 Dictionary를 통해서 Configuration에 입각한 OPEG 점수를 도출합니다.
        """
        return score["commit"] * score["cph"] \
             + score["issue"] * Config.opeg_issue \
             + score["license"] * Config.opeg_license \
             + score["pr"] * Config.opeg_pr \
             + score["contributor"] * Config.opeg_contributor \
             + score["branch"] * Config.opeg_branch


    @classmethod
    def get_cph(cls, soup, hours):
        """주어진 DOM 객체와 기준 시간으로 CPH를 계산합니다."""
        updated = soup.find_all('updated')
        current_time = datetime.utcnow()

        counting = 0
        for time in updated:
            updated_time = time.contents[0]
            timedelta = (current_time - datetime.strptime(updated_time, "%Y-%m-%dT%H:%M:%SZ")).total_seconds()
            if timedelta > 3600 * hours:
                return (0 if counting == 0 else counting - 1)
            else:
                counting += 1

        return 0 if counting == 0 else counting - 1

    @classmethod
    def process_url(cls, repo_list):
        """
        주어진 Repo 정보를 바탕으로 URL을 만듭니다.
        @return url_array 인식된 전체 Repo의 URL 리스트
        """
        url_array = list()
        github_prefix = "https://github.com/"

        for repo in repo_list:
            if repo.count("/") != 1:
                # Repository의 표현식에 오류가 있는 경우
                # 사전에 UI 단 입력에서 걸러줘야 하므로 여기서는 무시함
                continue
            url_array.append(github_prefix + repo)

        return url_array