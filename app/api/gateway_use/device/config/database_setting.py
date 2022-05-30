# coding=utf-8
#! /usr/bin/python

ROLE = "Gateway"
# ROLE = "Server"

if ROLE == "Gateway":
    mysql_config = {
        'host': 'localhost',
        'user': 'root',
        'password': 'kDd414o6',
        'db': 'lighting'
    }
    # mysql_config = {
    #     'host': 'localhost',
    #     'user': 'root',
    #     'password': 'f2f54321',
    #     'db': 'lighting_demo5'
    # }
elif ROLE == "Server":
    mysql_config = {
        'host': 'localhost',
        'user': 'root',
        'password': 'f2f54321',
        'db': 'lighting_demo5'
    }
else:
    mysql_config = {
        'host': 'localhost',
        'user': 'root',
        'password': 'f2f54321',
        'db': 'lighting_demo5'
    }

# Gateway Mac Address
uid = "09ea6335-d2bd-4678-9ca9-647b5574a09e"

# print(mysql_config)