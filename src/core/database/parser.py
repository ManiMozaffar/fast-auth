import base64
import datetime
import json
import uuid
from typing import Any

from pydantic import BaseModel


class JSONEncoder(json.JSONEncoder):
    def default(self, o: Any):
        if isinstance(o, (datetime.datetime, datetime.date, datetime.time)):
            return o.isoformat()
        elif isinstance(o, datetime.timedelta):
            return (datetime.datetime.min + o).time().isoformat()
        elif isinstance(o, uuid.UUID):
            return str(o)
        elif isinstance(o, BaseModel):
            return o.dict()
        elif isinstance(o, bytes):
            return base64.encodebytes(o).decode()

        return super(JSONEncoder, self).default(o)


class JSONDecoder(json.JSONDecoder):
    pass
