from models.results import Results
from models.stats import Stats
from models.teams import Team

from extensions import db


if __name__ == '__main__':
    db.create_all()
