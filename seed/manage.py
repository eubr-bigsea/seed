from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager

from seed.app import app
from seed.models import db

migrate = Migrate(app, db)
manager = Manager(app)

manager.add_command('db', MigrateCommand)
# manager.add_command('rq', flask_rq2)
if __name__ == "__main__":
    manager.run()
