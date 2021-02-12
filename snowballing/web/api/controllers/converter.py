__all__ = ['ConverterController']

from collections import namedtuple

from snowballing.utils import parse_bibtex
from snowballing.operations import bibtex_to_info
from snowballing import config

class ConverterController(object):
    """
    This controller handles requests for convert works from bibtex to
    json format.
    """

    @classmethod
    def bibtex(cls, bibtex):
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