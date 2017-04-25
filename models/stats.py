from extensions import db


class Stats(db.Model):

    __tablename__ = 'stats'

    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer)
    season = db.Column(db.String(128))
    off_rtg = db.Column(db.Float)
    def_rtg = db.Column(db.Float)
    pace = db.Column(db.Float)
    pt_diff = db.Column(db.Float)

    def __init__(self, team_id, season, off_rtg, def_rtg, pace, pt_diff):
        """
        Create an instance of the Stats model.
        """
        self.team_id = team_id
        self.season = season
        self.off_rtg = off_rtg
        self.def_rtg = def_rtg
        self.pace = pace
        self.pt_diff = pt_diff

    @classmethod
    def add(cls, stats):
        """
        Persist an instance of the Stats model.
        """
        db.session.add(stats)
        db.session.commit()
