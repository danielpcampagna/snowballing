__all__ = ['CitationController']

from snowballing.operations import load_citations, citation_text, reload
from ...helpers import prepare_citations
from snowballing.dbmanager import insert

class CitationController(object):
    @classmethod
    def create(cls, base_work_id, cited_work, backward=False):
        result_format = lambda work, cited, result: {"work": work, "cited": cited, "result": result}

        cited = {'pyref': cited_work}
        code = citation_text(workref=base_work_id, cited=cited, backward=backward)
        insert_result = insert(code, citations=cited_work).get("citations", [[]])[0]
        return result_format(
                    work=base_work_id,
                    cited=cited_work,
                    result=insert_result[3] if len(insert_result) == 4 else False,
                )

    @classmethod
    def read(cls, work_id=None, forward=True):
        citations = prepare_citations([c.__dict__ for c in load_citations()], forward=forward)
        if len(citations) == 0:
            reload()
            citations = prepare_citations([c.__dict__ for c in load_citations()], forward=forward)

        if work_id is not None:
            citations = {key: obj for key, obj in citations.items() if key == work_id}