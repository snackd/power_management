from .. import db


def generate_id(id_type, gateway_id):
    insert_generate_id_sql = "INSERT INTO `generate_id_list` (`id_type`, `gateway_id`) VALUES ({}, {})".format(id_type, gateway_id)
    insert_generate_id_result = db.engine.execute(insert_generate_id_sql)
    generate_id = insert_generate_id_result.lastrowid
    return generate_id


def last_demand_value(gateway_id):
    demand_last_sql = "SELECT `demand_min`, `demand_quarter`, `Total_value` FROM `electricity_list` " \
                      "WHERE `gateway_id` = {} ORDER BY `recorded_at` DESC LIMIT 1 ".format(gateway_id)
    demand_last = db.engine.execute(demand_last_sql).fetchall()
    return demand_last


def max_demand_value(gateway_id, begin_date, end_date='NOW()'):
    max_demand_sql = "SELECT `demand_min`, `demand_quarter`, `Total_value`, `recorded_at` FROM `electricity_list` " \
                     "WHERE `gateway_id` = {} AND `recorded_at` <= {} AND `recorded_at` >= '{}' " \
                     "ORDER BY `demand_quarter` DESC LIMIT 1 ".format(gateway_id, end_date, begin_date)
    max_demand = db.engine.execute(max_demand_sql).fetchall()
    return max_demand


def demand_setting_value(gateway_id):
    # demand_setting_list_sql = "SELECT `max_value`, `upper`, `lower`, `load_off_gap`, `reload_delay`, `reload_gap`, `cycle`, `mode`" \
    #                           " FROM `demand_setting` WHERE `gateway_id` = {}".format(gateway_id)
    demand_setting_list_sql = "SELECT `max_value`, `upper`, `lower`, `load_off_gap`, `reload_delay`, `reload_gap`, `cycle`, `mode`" \
                            " FROM `demand_setting_list` WHERE `gateway_id` = {}".format(gateway_id)
    demand_setting_list = db.engine.execute(demand_setting_list_sql).fetchall()
    return demand_setting_list


def demand_group_list(gateway_id):
    demand_group_list_sql = "SELECT `unload_group_id`, `name`, `num`, `unload_group_state` FROM `unload_group_list` WHERE `gateway_id` = {}".format(
        gateway_id)
    demand_group_list = db.engine.execute(demand_group_list_sql).fetchall()
    return demand_group_list

def demand_record_value(gateway_id, begin_date, end_date='NOW()'):
    demand_record_sql = "SELECT `demand_min`, `demand_quarter`, `Total_value`, `recorded_at` FROM `electricity_list` " \
                     "WHERE `gateway_id` = {} AND `recorded_at` <= {} AND `recorded_at` >= '{}' " \
                     "ORDER BY `recorded_at` ".format(gateway_id, end_date, begin_date)
    demand_record_list = db.engine.execute(demand_record_sql).fetchall()
    return demand_record_list

