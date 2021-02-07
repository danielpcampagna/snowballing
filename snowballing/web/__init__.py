# coding: utf-8
import os
import sys 
import importlib
import io
import traceback
from functools import wraps
from contextlib import redirect_stdout, redirect_stderr

from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from flasgger import Swagger

from ..collection_helpers import oget, dset
from ..utils import parse_bibtex
from ..snowballing import form_definition, WebNavigator
from ..operations import bibtex_to_info, load_work_map_all_years
from ..operations import work_to_bibtex, reload, find, work_by_varname, load_work, load_citations
from ..operations import should_add_info
from ..operations import invoke_editor, metakey
from .. import config
from .endpoints.citations import citations
from .endpoints.works import works
from .endpoints.converter import converter
from .helpers import general_jsonify, prepare_citations

if os.getcwd() not in sys.path:
    sys.path.append(os.getcwd())

import database #type: ignore

app = Flask(__name__)
app.register_blueprint(citations, url_prefix="/citations")
app.register_blueprint(works, url_prefix="/works")
app.register_blueprint(converter, url_prefix="/converter")
CORS(app)

swagger = Swagger(app)

LOADED_DB = False
STATUS = set()
SCHOLAR_IDS = {}
CLUSTER_IDS = {}

def load_db():
    global LOADED_DB
    importlib.reload(database)
    def populate_scholar(work, metakey):
        config.check_load(work, metakey, warning=lambda x: STATUS.add(x))
        scholar_ids = oget(work, "scholar_id", "", cvar=config.SCHOLAR_MAP)
        if not isinstance(scholar_ids, (list, tuple)):
            scholar_ids = [scholar_ids]
        for sid in scholar_ids: 
            SCHOLAR_IDS[sid] = work
        cluster_ids = oget(work, "cluster_id", "", cvar=config.SCHOLAR_MAP)
        if not isinstance(cluster_ids, (list, tuple)):
            cluster_ids = [cluster_ids]
        for cid in cluster_ids: 
            CLUSTER_IDS[cid] = work
    reload(work_func=populate_scholar)
    if "" in SCHOLAR_IDS:
        del SCHOLAR_IDS[""]
    if "" in CLUSTER_IDS:
        del CLUSTER_IDS[""]
    LOADED_DB = True


def find_work_by_scholar(scholar):
    if not LOADED_DB:
        load_db()
    
    work = SCHOLAR_IDS.get(scholar.get("scholar_id", None), None)
    if work:
        return work
    work = CLUSTER_IDS.get(scholar.get("cluster_id", None), None)
    if work:
        return work
    return None


def latex_to_info(latex):
    if latex is not None:
        entries = parse_bibtex(latex)
        try:
            info = bibtex_to_info(entries[0], config.BIBTEX_TO_INFO_WITH_TYPE)
            return info
        except:
            return None


def unified_find(info, scholar, latex, db_latex, citation_var, citation_file, backward):
    try:
        citation_work = work_by_varname(citation_var)
        if citation_var and not citation_work:
            STATUS.add("[Error] Citation var {} not found".format(citation_var))

        work = None
        db_latex = None
        if latex is not None:
            info = latex_to_info(latex)
        if info is None and db_latex is not None:
            info = latex_to_info(db_latex)

        work = find_work_by_scholar(scholar)
        if work is not None and info is None:
            info = latex_to_info(work_to_bibtex(work))
        
        pyref = None
        if info is not None and type(info) is dict:
            for key, value in scholar.items():
                if value is not None:
                    info[config.SCHOLAR_MAP.get(key, key)] = value
            
            should, work, info = should_add_info(
                info, citation_work, article=None,
                backward=backward, citation_file=citation_file,
                warning=lambda x: STATUS.add("[Warning]" + x),
                add_citation=bool(citation_var),
                bibtex_rules=config.BIBTEX_TO_INFO_IGNORE_SET_ID
            )

            if work is not None:
                pyref = work @ metakey
                dset(info, "pyref", pyref)
            
        
        else:
            should = {
                "add": True,
                "citation": citation_work,
                "set": {},
                "backward": backward
            }
        
        if work:
            if not db_latex:
                db_latex = work_to_bibtex(work)
            if not latex:
                latex = db_latex
            if pyref is None:
                pyref = getattr(work, 'metakey')

        
        return {
            "result": "ok",
            "msg": "",
            "found": bool(work),
            "info": info,
            "pyref": pyref,
            "latex": latex,
            "db_latex": db_latex,
            "citation": bool(should["citation"]),
            "add": should["add"],
            "status": list(STATUS),
        }, work, should
    except Exception as e:
        traceback.print_exc()
        return {
            "result": "error",
            "msg": repr(e),
            "status": list(STATUS),
        }, None, None


def unified_exc(message, reload=False):
    def unified_dec(func):
        @wraps(func)
        def dec():
            result = dict()
            try:
                if reload:
                    load_db()
                    importlib.reload(database)
                result, work, should_add = unified_find(
                    request.json.get("info"),
                    {
                        "scholar_id": request.json.get("scholar_id"), # e.g., "scholar_id": "ucciVefuv0sJ",
                        "cluster_id": request.json.get("cluster_id"), # e.g., "cluster_id": "5458343950729529273",
                        "scholar": request.json.get("scholar"),       # e.g., "scholar": "http://scholar.google.com/scholar?cites=5458343950729529273&as_sdt=2005&sciodt=0,5&hl=en",
                        "scholar_ok": request.json.get("scholar_ok"), # e.g., "scholar_ok": true,
                    },
                    request.json.get("latex"),
                    request.json.get("db_latex"),
                    request.json.get("citation_var"),
                    request.json.get("citation_file"),                # e.g., "citation_file": "murta2014a",
                    request.json.get("backward"),
                )
                result = func(result, work, should_add)
            except Exception as e:
                result["msg"] = message + ": " + repr(e)
                traceback.print_exc()
            if result["msg"]:
                result["result"] = "error"
            return jsonify(result)
        return dec
    return unified_dec


@app.route("/ping", methods=["GET", "POST"])
def ping():
    return {
        "result": "ok",
        "msg": "",
    }


@app.route("/find", methods=["GET", "POST"])
@unified_exc("Unable to find work")
def find_work(result, work, should_add):
    return result


@app.route("/click", methods=["GET", "POST"])
@unified_exc("Unable to open editor")
def do_click(result, work, should_add):
    if work:
        invoke_editor(work)
    else:
        result["msg"] = "Work not found"
    return result


@app.route("/form", methods=["GET", "POST"])
@unified_exc("Unable to load form", reload=True)
def form(result, work, should_add):
    result["form"] = form_definition()
    return result

@app.route("/form/submit", methods=["GET", "POST"])
@unified_exc("Unable to submit form", reload=True)
def submit_form(result, work, should_add):
    if result["result"] == "ok":
        info = result["info"]
        backward = request.json.get("backward") or ""
        values = request.json.get("values")
        citation_var = request.json.get("citation_var")
        citation_file = request.json.get("citation_file")
        navigator = WebNavigator(
            values, work, info,
            citation_file=citation_file,
            citation_var=citation_var,
            backward=backward,
            should_add=should_add,
        )
        result["form"] = form_definition()
        result["resp"] = navigator.show()
    return result

@app.route("/run", methods=["GET", "POST"])
def run():
    try:
        error = False
        out = io.StringIO()
        err = io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                exec(request.json.get("code"))
            except:
                traceback.print_exc()
                error = True
        return jsonify({
            "stdout": out.getvalue(),
            "stderr": err.getvalue(),
            "error": error,
            "result": "ok",
            "msg": "",
            "status": list(STATUS),
        })
    except Exception as e:
        return jsonify({
            "result": "error",
            "msg": "Unable to run code: " + repr(e),
            "status": list(STATUS),
        })


@app.route("/clear", methods=["GET", "POST"])
def clear():
    load_db()
    STATUS.clear()
    return jsonify({
        "result": "ok",
        "msg": "",
        "status": list(STATUS),
    })

@app.route("/database", methods=["GET"])
def get_database():
    """Example endpoint returning a list of works and citations.
    ---
    parameters:
      - in: header
        name: forward
        type: boolean
        required: false
        default: true
    definitions:
      Citation:
        name: citation
        type: object
        example: {
            "freire2008a": {
                "context": [
                    null
                ],
                "ref": [
                    "5"
                ],
                "work": [
                    "murta2014a"
                ]
            },
        }
        properties:
          work_identification:
            type: object
            description: This object key is the work identification (e.g., "freire2008a").
            properties:
              context:
                type: array
                description: The context of the n-th work.
                items:
                  type: string
              ref:
                type: array
                description: The position in the work references section of the n-th work.
                items:
                  type: string
              work:
                type: array
                description: The citations (where header forward is true) / cited list (where header forward is false) of the <work_identification.. (e.g. Where murta2014a cites freire2008a and header "forward" is true, it's expected "murta2014a" be included in this property value)
                items:
                  type: string
      Work:
        name: work
        type: object
        example: {
            "aliases": [
                [
                2015,
                "noWorkflow: Capturing and Analyzing Provenance of Scripts",
                "Chirigati, Fernando and Koop, David and Freire, Juliana"
                ]
            ],
            "approach_name": "noWorkflow",
            "authors": "Murta, Leonardo and Braganholo, Vanessa and Chirigati, Fernando and Koop, David and Freire, Juliana",
            "category": "snowball",
            "citation_file": "murta2014a",
            "cluster_id": "5458343950729529273",
            "display": "no  Work  flow",
            "entrytype": "inproceedings",
            "file": "murta2014a.pdf",
            "local": "Cologne, Germany",
            "metakey": "murta2014a",
            "name": "noWorkflow: capturing and analyzing provenance of scripts",
            "organization": "Springer",
            "pp": "71--83",
            "scholar": "http://scholar.google.com/scholar?cites=5458343950729529273&as_sdt=2005&sciodt=0,5&hl=en",
            "scholar_id": "ucciVefuv0sJ",
            "scholar_ok": true,
            "tracking": "alert",
            "year": 2014
        }
        properties:
          ID:
            type: string
            required: false
          aliases:
            type: array
            required: false
            items:
              type: array
              items:
                type: string|integer
          approach_name:
            type: string
            required: false
          authors:
            type: string
            required: false
          category:
            type: string
            required: false
          citation_file:
            type: string
            required: false
          cluster_id:
            type: string
            required: false
          display:
            type: string
            required: false
          doi:
            type: string
            required: false
          due:
            type: string
            required: false
          entrytype:
            type: string
            required: false
          file:
            type: string
            required: false
          local:
            type: string
            required: false
          metakey:
            type: string
            required: false
          month:
            type: string
            required: false
          name:
            type: string
            required: false
          number:
          organization:
            type: string
            required: false
          pp:
            type: string
            required: false
          publisher:
            type: string
            required: false
          scholar:
            type: string
            required: false
          scholar_id:
            type: string
            required: false
          scholar_ok:
            type: boolean
            required: false
          star:
            type: string
            required: false
          tracking:
            type: string
            required: false
          volume:
            type: string
            required: false
          year:
            type: string
            required: false
    responses:
      200:
        description: A JSON array of user names
        schema:
          properties:
            citations:
              $ref: '#/definitions/Citation'
            works:
              type: array
              items:
                $ref: '#/definitions/Work'
    """
    global LOADED_DB
    # global SCHOLAR_IDS
    # global CLUSTER_IDS
    forward = not request.headers.get("Forward", "true").lower() == "false"

    if not LOADED_DB:
        load_db()

    # SCHOLAR = [general_jsonify(SCHOLAR_IDS[k]) for k in SCHOLAR_IDS]
    # CLUSTER = [general_jsonify(CLUSTER_IDS[k]) for k in CLUSTER_IDS]
    citations = prepare_citations([c.__dict__ for c in load_citations()], forward=forward)
    works = [general_jsonify(w) for w in load_work()]

    return jsonify({
        # "scholar": SCHOLAR,
        # "cluster": CLUSTER,
        "citations": citations,
        "works": works,
    })

if __name__ == "__main__":
    app.run()

