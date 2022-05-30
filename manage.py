# coding=utf-8

import os
# from app.models import User
from app import create_app, db
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand
from redis import Redis


app = create_app(os.getenv('FLASK_CONFIG', 'default'))

manager = Manager(app)
migrate = Migrate(app, db)
dict_map = dict(app=app, db=db)


def make_shell_context():
    return dict(app=app, db=db, Demand=Demand, Setting=Setting, Gatewayid=Gatewayid)


manager.add_command("shell", Shell(make_context=dict_map))
manager.add_command('db', MigrateCommand)

cli = Redis('localhost')

if __name__ == '__main__':
    manager.run()
