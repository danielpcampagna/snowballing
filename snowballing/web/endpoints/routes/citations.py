__all__ = ['citations']

from flask import Blueprint, request, jsonify

from snowballing.operations import load_citations, citation_text, reload
from ...helpers import prepare_citations
from ..controllers import CitationController

import importlib
import database #type: ignore

citations = Blueprint("citations", __name__)
importlib.reload(database)

BACKWARD_KEYWORD = 'backward_citation'
FORWARD_KEYWORD = 'forward_citation'

@citations.route("/<work_id>/", methods=["POST"])
def create(work_id):
    backward_workrefs = request.json.pop(BACKWARD_KEYWORD, None)
    forward_workrefs  = request.json.pop(FORWARD_KEYWORD, None)
    result = {
        BACKWARD_KEYWORD: list(),
        FORWARD_KEYWORD:  list(),
    }

    if backward_workrefs is None and forward_workrefs is None:
        return jsonify({
            "error": "No citation was created."
        })

    for work in backward_workrefs:
        result[BACKWARD_KEYWORD].append(CitationController.create(base_work_id=work_id, cited_work=work, backward=True))
    
    for work in forward_workrefs:
        result[FORWARD_KEYWORD].append(CitationController.create(base_work_id=work_id, cited_work=work, backward=False))

    return result

@citations.route("/", methods=["GET"], defaults={"work_id": None})
@citations.route("/<work_id>/", methods=["GET"])
def read(work_id):
    forward = not request.headers.get("Forward", "true").lower() == "false"
    citations = CitationController.read(work_id, forward=forward)
    return jsonify(citations)