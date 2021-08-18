def make_request(req, fields=[], params={}):
    result = []
    response = req(fields=fields, params=params, pending=True).execute()
    for item in response:
        if isinstance(response.params, list):
            response.params = {}
        result.append(item.export_all_data())
    return result
