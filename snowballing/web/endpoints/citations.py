
from flask import Blueprint, request, jsonify

from snowballing.operations import load_citations, citation_text, reload
from snowballing.dbmanager import insert
from ..helpers import general_jsonify, prepare_citations

import importlib
import database #type: ignore

citations = Blueprint("citations", __name__)
importlib.reload(database)

@citations.route("", methods=["POST"])
@citations.route("/", methods=["POST"])
def create():

    workref           = request.json.pop('workref')
    backward_workrefs = request.json.pop('backwards', None)
    forward_workrefs  = request.json.pop('forwards', None)
    result = {
        'backwards': list(),
        'forwards':  list(),
    }
    result_format = lambda work, cited, result: {"work": work, "cited": cited, "result": result}

    if backward_workrefs is None and forward_workrefs is None:
        return jsonify({
            "error": "No citation was created."
        })

    for work in backward_workrefs:
        cited = {'pyref': work}
        code = citation_text(workref=workref, cited=cited, backward=True)
        insert_result = insert(code, citations=work).get("citations", [[]])[0]
        result['backwards'].append(result_format(
                    work=workref,
                    cited=work,
                    result=insert_result[3] if len(insert_result) == 4 else False,
                ))
    
    for work in forward_workrefs:
        cited = {'pyref': work}
        code = citation_text(workref=workref, cited=cited)
        insert_result = insert(code, citations=work).get("citations", [[]])[0]
        result['forwards'].append(result_format(
                    work=work,
                    cited=workref,
                    result=insert_result[3] if len(insert_result) == 4 else False,
                ))

    return result

@citations.route("/", methods=["GET"], defaults={"citation_id": None})
@citations.route("/<citation_id>/", methods=["GET"])
def read(citation_id):
    forward = not request.headers.get("Forward", "true").lower() == "false"

    if citation_id is not None:
        return f"Only the citation with ID {citation_id}"
    
    citations = prepare_citations([c.__dict__ for c in load_citations()], forward=forward)
    if len(citations) == 0:
        reload()
        citations = prepare_citations([c.__dict__ for c in load_citations()], forward=forward)

    return jsonify({
        "citations": citations
    })