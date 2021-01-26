import importlib
import database

from flask import Blueprint, request, jsonify

from snowballing.utils import parse_bibtex
from snowballing.operations import load_citations, bibtex_to_info
from snowballing import config

converter = Blueprint("converter", __name__)
importlib.reload(database)

@converter.route("/bibtex", methods=["POST"])
def bibtex():
    inputbibtex = request.data
    
    result = []
    incomplete = []
    for entry in parse_bibtex(inputbibtex):
        try:
            info = bibtex_to_info(entry, config.BIBTEX_TO_INFO_WITH_TYPE)
            result.append(info)
        except Exception as e:
            print(repr(e))
            # result.append("Incomplete")
            incomplete.append({
                "entry": entry,
                "error": repr(e),
            })

    return jsonify({
        'meta': {
            'total':      len(result) - len(incomplete),
            'errors':     len(incomplete),
            "incomplete": incomplete
        },
        'data': result,
    })
