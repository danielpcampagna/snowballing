__all__ = ["works"]

from flask import Blueprint, json, request, jsonify

from snowballing.operations import load_work, reload, info_to_code#, create_info_code
from snowballing.dbmanager import insert
from ...helpers import general_jsonify
from .helpers import valid_articles, Converter

import importlib
import database # type: ignore

works = Blueprint("works", __name__)
importlib.reload(database)

HEADER_FORMAT_NAME = "Format"
HEADER_FORMAT_VALUE_BIBTEX = "bibteX"
HEADER_FORMAT_VALUE_JSON = "json"

@works.route("/", methods=["POST"])
def create():
    """ Create new works from bibtex format. """
    print(request.json)

    headers = request.headers
    articles = []

    if headers.get(HEADER_FORMAT_NAME) == HEADER_FORMAT_VALUE_BIBTEX:
        converter   = Converter(request.data)
        articles    = converter.convert()
        if converter.has_error():
            # TODO: handle this error properly
            return "Error when converting BibTeX"
    elif headers.get(HEADER_FORMAT_NAME) == HEADER_FORMAT_VALUE_JSON:
        articles = request.json
    else:
        # TODO: handle this error properly
        return f"Error because the '{HEADER_FORMAT_NAME}' header is missing."

    result = list()
    for article in articles:
        code = info_to_code(article)
        result.append(insert(code))

    return jsonify(result)

@works.route("/", methods=["GET"], defaults={"work_id": None})
@works.route("/<work_id>/", methods=["GET"])
def read(work_id):
    
    result = [general_jsonify(w) for w in load_work()]
    if len(result) == 0:
        reload()
        result = [general_jsonify(w) for w in load_work()]
    
    if work_id is not None:
        result = [w for w in result if w.get("ID") == work_id]

    return jsonify({
        "works": result
    })

# @works.route("/validate", methods=["POST"])
# def validate():
#     result = list()
#     for article, nwork, info, should in valid_articles(articles, show=True):
#         result.append({
#             "article": article,
#             "nwork": nwork,
#             "info": info,
#             "should": should,
#         })
#         citation_var = article.get('citation_var', None)
#         citation_file = article.get('citation_file', None)