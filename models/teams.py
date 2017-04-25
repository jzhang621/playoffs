from extensions import db


class Team(db.Model):

    __tablename__ = 'teams'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True)

    def __init__(self, name):
        """
        Create an instance of the Team model.

        :param str name: The name of the team (e.g. "SAC")
        """
        self.name = name

    @classmethod
    def get_or_create(cls, name):
        """
        Get or create the Team object associated with the given name

        :param str name: The name of the team (e.g. "SAC")
        """
        team = db.session.query(cls).filter(Team.name == name).first()
        if not team:
            team = Team(name)
            db.session.add(team)
            db.session.commit()
        return team

    @classmethod
    def get_id_by_name(cls, name):
        """
        Given a short name, return the id of the team.

        :param str name: The short name of the team (e.g. "SAC").
        :return: The team id.
        """
        return db.session.query(Team.id).filter(Team.name == name).scalar()

    @classmethod
    def get_name_by_id(cls, team_id):
        """
        Given an id, return the name of the team.

        :param int id: The team id
        :return: The short name of the team (e.g. "SAC").
        """
        team = db.session.query(Team.name).filter(Team.id == team_id).first()
        return team.name
