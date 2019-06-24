from flask import Flask
from app.crawler import crawler_run, CrawlerThread
import atexit

from apscheduler.schedulers.background import BackgroundScheduler

def create_app(config):
    app = Flask(__name__)
    app.config.from_object(config)

    # 최초 Crawling Job 등록
    first_thread = CrawlerThread(1, "first_time_trigger", 1)
    first_thread.start()

    scheduler = BackgroundScheduler()
    scheduler.add_job(crawler_run, trigger='interval', minutes=10)
    scheduler.start()

    atexit.register(lambda: scheduler.shutdown())

    from .web import web as web_blueprint
    from .restful import restful as restful_blueprint

    app.register_blueprint(web_blueprint)
    app.register_blueprint(restful_blueprint)

    return app
