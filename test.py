import json


action = "insert"
action = "update"
action = "delete"

table = "area_list"
table = "group_list"
table = "node_list"

payload2 = json.dumps(payload)

payload = {
    "schedule_id":1,
    "group_id":1,
    "group_state":0,
    "control_time":"08:00:00",
    "holiday":1,
    "sunrise":None,
    "offload":1,
}
payload = {
    "area_id":1,
    "node_id":1,
}


if action == 'update':
    sql = "UPDATE `{}` SET ".format(table)
    i = 0
    column = payload.get("column")
    for key, value in column.items():
        i += 1
        sql += " `{}`= '{}'".format(key, value)
        if i == (len(column)):
            break
        elif i != (len(column)):
            sql += ","
    sql += " WHERE "
    where = payload.get("where")
    i = 0
    for key, value in where.items():
        sql += " `{}`= '{}'".format(key, value)
        i += 1
        if i != len(where):
            sql += " AND"

print(sql)

if action == 'insert':
    sql = "INSERT INTO `{}`(".format(table)
    i = 0
    for key in payload.keys():
        i += 1
        sql += " `{}`".format(key)
        if i != len(payload):
            sql += ","
    sql += ") VALUES ("
    i = 0
    for value in payload.values():
        i += 1
        sql += " '{}'".format(value)
        if i != len(payload):
            sql += ","
    sql += ")"

print(sql)

payload ={
    "column":{
        "max_vaule":1,
        "upper":1,
        "lower":1,
        "load_off_gap":1,
        "reload_delay":1,
        "reload_gap":1,
        "cycle":1,
        "groups":1,
        "mode":1,
    },
    "where": {
        "demand_id":1,
    },
}
payload =
{
    "demand_id":1,
}