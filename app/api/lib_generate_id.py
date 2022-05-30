from .. import db


def generate_id(id_type, gateway_id):
    insert_generate_id_sql = "INSERT INTO `generate_id_list` (`id_type`, `gateway_id`) VALUES ({}, {})".format(id_type, gateway_id)
    insert_generate_id_result = db.engine.execute(insert_generate_id_sql)
    generate_id = insert_generate_id_result.lastrowid
    return generate_id
