from .. import db


def get_gateway_info(gateway_id):
    get_gateway_info_sql = "SELECT `id`, `mac_address`, `name` FROM `gateway_list` WHERE `id`={}".format(gateway_id)
    get_gateway_info_result = db.engine.execute(get_gateway_info_sql).fetchall()
    return get_gateway_info_result
