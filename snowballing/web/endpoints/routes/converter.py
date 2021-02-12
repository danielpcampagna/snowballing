# __all__ = ['converter']

# import importlib
# import database #type: ignore

# from flask import Blueprint, request, jsonify

# from snowballing.utils import parse_bibtex
# from snowballing.operations import bibtex_to_info
# from snowballing import config
# from ..controllers import WorkController

# converter = Blueprint("converter", __name__)
# importlib.reload(database)

# @converter.route("/bibtex", methods=["POST"])
# def bibtex():
#     inputbibtex = request.data
#     result, incomplete = WorkController.convert(inputbibtex)

#     return jsonify({
#         'meta': {
#             'total':      len(result),
#             'errors':     len(incomplete),
#             "incomplete": incomplete
#         },
#         'data': result,
#     })
