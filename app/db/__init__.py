from tinydb import TinyDB, where
from tinydb.operations import delete
from config import Config

class Database:
    db = TinyDB(Config.tinydb_document)
    team = db.table('team')

    @classmethod
    def get_info(cls, name):
        """
        한 팀의 점수와 자세한 정보를 가져옵니다.
        """
        result = cls.team.search(where('name') == name)

        if len(result) == 0: 
            return False
        
        return result[0].copy()

    @classmethod
    def get_all(cls):
        """
        모든 팀의 점수를 가져옵니다.
        """
        return cls.team.all()

    @classmethod
    def get_chart_data(cls):
        """
        Chart.js용 데이터를 생성합니다.
        """
        all_team = cls.team.all()
        team_name_list = list()
        team_score_list = list()
        background_color_list = list()
        border_color_list = list()
        count = 0

        for team in all_team:
            count = count % len(Config.background_color)
            team_name_list.append(team["name"])
            team_score_list.append(team["score"])
            background_color_list.append(Config.background_color[count])
            border_color_list.append(Config.border_color[count])
            count += 1
        return {
            "names": team_name_list,
            "scores": team_score_list,
            "backgrounds": background_color_list,
            "borders": border_color_list
        }

    @classmethod
    def set_info(cls, score):
        """
        한 팀의 점수와 자세한 정보를 세팅합니다.
        """
        # if cls.team.get(where('name') == score["name"]) != None:
        #     cls.team.remove(where('name') == score["name"])
        return cls.team.upsert(score, where('name') == score["name"])
