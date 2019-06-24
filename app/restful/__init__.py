from flask import Blueprint
from flask_restful import Api

restful = Blueprint('restful', __name__, url_prefix='/api')
api_restful = Api(restful)

# api_restful.add_resource(class)