import warnings
from snowballing.operations import create_info_code, should_add_info, bibtex_to_info
from snowballing.utils import parse_bibtex
from snowballing import config

def valid_articles(articles, show=False, **context):
    """Generate valid articles"""
    if not articles:
        return

    # work = work_by_varname(citation_var)
    # citation_file = citation_file or oget(work, "citation_file", citation_var)

    work = context.pop('work', None)
    backward = context.pop('backward', True)
    citation_file = context.pop('citation_file', None)
    force_citation_file = context.pop('force_citation_file', False)
    warnings = []

    for article in articles:
        should, nwork, info = should_add_info(
            article, work, article=article,
            backward=backward,
            citation_file=citation_file if force_citation_file else None,
            warning=lambda x: warnings.append(x)
        )

        if should["add"]:
            yield article, nwork, info, should

class Converter:
    """ Convert Bibtex to the used format. """
    def __init__(self, articles):
        self.input_articles = articles
        self.clear()
    
    def clear(self):
        self.errors = []
        self.articles = []

    def convert(self):
        self.clear()

        for entry in parse_bibtex(self.input_articles):
            try:
                info = bibtex_to_info(entry, config.BIBTEX_TO_INFO_WITH_TYPE)
                self.articles.append(info)
            except Exception as e:
                print(repr(e))
                self.errors.append({
                    "entry": entry,
                    "error": repr(e),
                })

    def has_error(self):
        return len(self.errors) > 0