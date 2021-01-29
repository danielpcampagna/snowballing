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

def prepare_citations(citations, forward=True):
        result = dict()
        for item in citations:
            work     = item.get("work")
            citation = item.get("citation")
            ref      = item.get("ref")
            context  = item.get("context")

            work_id, metakey_id = (getattr(work, "metakey", None), getattr(citation, "metakey", None))
            key, value = (metakey_id, work_id) if forward else (work_id, metakey_id)

            if key not in result:
                result[key] = {
                    "context": [],
                    "ref": [],
                    "work": [],
                }

            result[key]["context"].append(context)
            result[key]["ref"].append(ref)
            result[key]["work"].append(value)
        return result