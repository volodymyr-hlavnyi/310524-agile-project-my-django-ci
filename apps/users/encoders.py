import json
from apps.users.choices.positions import UserPositions

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, UserPositions):
            return o.value
        if isinstance(o, set):
            return list(o)
        return super().default(o)