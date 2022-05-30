import os
import json
import math
import time
import datetime
from decimal import Decimal
from datetime import timedelta
from operator import attrgetter, itemgetter

from flask import json, jsonify, request
from sqlalchemy import and_, between, exists, func, or_

from . import api
from .. import db
from ..models import *

from config import role

def log_info(gatewayuid, action, content, insert_data, execute_state, role):
    insert_log = Log(
        None,
        gatewayuid,
        action,
        content,
        insert_data,
        execute_state,
        datetime.datetime.now(),
        role
    )
    db.session.add(insert_log)
    db.session.commit()
