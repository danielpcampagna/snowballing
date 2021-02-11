
from flask import Blueprint, request, jsonify

from snowballing.operations import load_citations, citation_text, reload
from snowballing.dbmanager import insert
from ..helpers import general_jsonify, prepare_citations

import importlib
import database #type: ignore

citations = Blueprint("citations", __name__)
importlib.reload(database)

@citations.route("/<work_id>", methods=["POST"])
def create(work_id):
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
        code = citation_text(workref=work_id, cited=cited, backward=True)
        insert_result = insert(code, citations=work).get("citations", [[]])[0]
        result['backwards'].append(result_format(
                    work=work_id,
                    cited=work,
                    result=insert_result[3] if len(insert_result) == 4 else False,
                ))
    
    for work in forward_workrefs:
        cited = {'pyref': work}
        code = citation_text(workref=work_id, cited=cited)
        insert_result = insert(code, citations=work).get("citations", [[]])[0]
        result['forwards'].append(result_format(
                    work=work,
                    cited=work_id,
                    result=insert_result[3] if len(insert_result) == 4 else False,
                ))

    return result

@citations.route("/", methods=["GET"], defaults={"work_id": None})
@citations.route("/<work_id>", methods=["GET"])
def read(work_id):
    forward = not request.headers.get("Forward", "true").lower() == "false"
    
    citations = prepare_citations([c.__dict__ for c in load_citations()], forward=forward)
    if len(citations) == 0:
        reload()
        citations = prepare_citations([c.__dict__ for c in load_citations()], forward=forward)

    if work_id is not None:
        citations = {key: obj for key, obj in citations.items() if key == work_id}

    return jsonify(citations)