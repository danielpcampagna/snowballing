
__all__ = ['WorkController']

from collections import namedtuple

from snowballing.operations import info_to_code
from snowballing.dbmanager import insert
from snowballing.operations import should_add_info, bibtex_to_info, load_work, reload
from snowballing.utils import parse_bibtex
from snowballing import config

from ...helpers import general_jsonify

def validate_articles(articles):
    """Validate articles"""
    if not articles:
        return

    ValidatedArticle = namedtuple('ValidatedArticle', ['article', 'valid', 'warnings'])
    result = list()

    for article in articles:
        warnings = list()
        
        work = article.get('metakey', None)
        backward = article.pop('backward', True)
        citation_file = article.pop('citation_file', None)
        force_citation_file = article.pop('force_citation_file', False)
        try:
            _, _, _ = should_add_info(
                article, work, article=article,
                backward=backward,
                citation_file=citation_file if force_citation_file else None,
                warning=lambda x: warnings.append(x)
            )

            result.append(ValidatedArticle(article=article, valid=True, warnings=warnings))
        except Exception as e:
            warnings.append(str(e))
            result.append(ValidatedArticle(article=article, valid=False, warnings=warnings))
    return result

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

class WorkController(object):
    @classmethod
    def create(cls, article):
        code = info_to_code(article)
        return insert(code)
    
    @classmethod
    def read(cls, work_id=None):
        result = [general_jsonify(w) for w in load_work()]
        if len(result) == 0:
            reload()
            result = [general_jsonify(w) for w in load_work()]
        
        if work_id is not None:
            result = [w for w in result if w.get("ID") == work_id]

    @classmethod
    def convert(cls, bibtex):
        """
        This method handles requests to convert a work from bibtex to json
        format.
        """
        # from .work import Converter
        # converter   = Converter(data)
        # articles    = converter.convert()
        ConvertedResult = namedtuple('ConvertedResult',['result','incomplete'])

        result = []
        incomplete = []
        for entry in parse_bibtex(bibtex):
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
        return ConvertedResult(result, incomplete)
    
    @classmethod
    def validate(cls, articles):
        result = []
        for validated_article in validate_articles(articles):
            result.append(validated_article)
        return result