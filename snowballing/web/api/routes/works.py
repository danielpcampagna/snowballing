__all__ = ["works"]

from snowballing.web.endpoints.controllers.work import WorkController
from flask import Blueprint, json, request, jsonify, make_response, current_app

from ..controllers import WorkController

import importlib
import database # type: ignore

works = Blueprint("works", __name__)
importlib.reload(database)

@works.route("/", methods=["POST"])
def create():
    """ Create new works from json format. """

    articles = request.json
    result = list()
    for article in articles:
        result.append(WorkController.create(article))

    return jsonify(result)

@works.route("/", methods=["GET"], defaults={"work_id": None})
@works.route("/<work_id>/", methods=["GET"])
def read(work_id):
    
    result = WorkController.read(work_id)
    return jsonify(result)

@works.route("/convert/", methods=["POST"])
def convert():
    inputbibtex = request.data
    result, incomplete = WorkController.convert(inputbibtex)

    return jsonify({
        'meta': {
            'total':      len(result),
            'errors':     len(incomplete),
            "incomplete": incomplete
        },
        'data': result,
    })


@works.route("/validate/", methods=["POST"])
def validate():
    articles = request.json
    if type(articles) is not list:
        articles = [articles]
    result = [art for art in WorkController.validate(articles=articles) if not art.valid]
    
    response = make_response('', 204) if len(result) == 0 else make_response(jsonify(result), 200)
    # response.mimetype = current_app.config['JSONIFY_MIMETYPE']
    return response