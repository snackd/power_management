from flask import Blueprint

api = Blueprint('api', __name__)

# from . import project, area, node, group, scene, mqtt_talker, device, festival, schedule, file, \
#     demand_setting, demand_group_setting, demand_dashboard, nbiot_response

from . import project, area, node, group, scene, mqtt_talker, file, \
    demand_setting, demand_group_setting, demand_dashboard, nbiot_response
