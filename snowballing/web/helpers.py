def general_jsonify(obj):
    primitive = (int, str, bool, list)

    def is_primitive(thing):
        return isinstance(thing, primitive)

    if obj is None:
            return None

    public_keys = [key for key in dir(obj) if not key.startswith("_")]
    result = dict()
    for key in public_keys:
        attribute_value = getattr(obj, key, None)
        
        if attribute_value is not None and not callable(attribute_value):
            if is_primitive(attribute_value):
                result[key] = attribute_value
            elif type(attribute_value) is dict:
                result[key] = general_jsonify(attribute_value)
    return result

def prepare_citations(citations):
    result = dict()
    for citation in citations:
        citation_id = citation["citation"].get("ID") or citation["citation"].get("metakey", None)
        # context = citation["context"]
        # ref = citation["ref"]
        work_id = citation["work"]["ID"]

        if citation_id not in result:
            result[citation_id] = {
                # "context": [],
                # "ref": [],
                "work": [],
            }