from extensions import db


class Results(db.Model):

    __tablename__ = 'results'

    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer)
    game_num = db.Column(db.Integer)
    opp_id = db.Column(db.Integer)
    points_for = db.Column(db.Integer)
    points_against = db.Column(db.Integer)
    season = db.Column(db.String(40))

    def __init__(self, team_id, game_num, opp_id, points_for, points_against, season):
        """
        Create an instance of the Results model.
        """
        self.team_id = team_id
        self.game_num = game_num
        self.opp_id = opp_id
        self.points_for = points_for
        self.points_against = points_against
        self.season = season
