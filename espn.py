#!/usr/bin/env python

"""
This is my simple library to scrape NBA and NCB play-by-play information from
ESPN. I needed a small project to test out BeautifulSoup Alpha 4, so I felt
this was a good opportunity to refine some earlier code I had written.

In order to use this, you will need to download bs4 and also lxml (bs4 is
modular and can use both lxml and html5lib as back-end parsers).

The output is in dictionary format and contains the following information for
each individual play: quarter, quarter_time, overall_time, home_score,
away_score, home_play, away_play, and official_play (for timeouts, starts of
quarters, etc). I've found the majority of games normally have around 400 to
460 plays.

"""
from collections import defaultdict
import click
import json
import requests
import re
import datetime
import pprint
from urlparse import urlparse
from bs4 import BeautifulSoup as bs


def daterange(start, end):
    """Generator for days between two specific days."""
    for n in range((end - start).days):
        yield start + datetime.timedelta(n)


def _format_scoreboard_url(day, league='nba'):
    """Format ESPN scoreboard link to scrape individual box scores from."""
    league = league.lower()
    link = [league + '/scoreboard?date=']
    if isinstance(day, datetime.date):
        link.append(day.strftime('%Y%m%d'))
    else:
        link.append(day)
    if league == 'ncb':
        link.append('&confId=50')
    scoreboard_link = ''.join(['http://scores.espn.go.com/', ''.join(link)])
    return scoreboard_link


def scrape_links(espn_scoreboard):
    """Scrape ESPN's scoreboard for Play-By-Play links."""
    url = urllib2.urlopen(espn_scoreboard)
    print url.geturl()
    soup = bs(url.read(), 'lxml')
    div = soup.find('div', {'class': 'span-4'})
    links = (a['href'] for a in div.findAll('a') if re.match('Play.*',
        a.contents[0]))
    queries = [urlparse(link).query for link in links]
    return queries


def adjust_game(plays, league='nba'):
    """
    Takes plays from parse_plays (generator of lists) and the league which
    it is parsing (used for correct quarter/halve time). It returns a list
    of plays in dictionary format -- which is more convenient for lookups.

    The dictionary contains the following information: quarter, quarter_time,
    overall_time, home_score, away_score, home_play, away_play, and
    official_play (for timeouts, starts of quarters, etc).
    """
    # TODO: Maybe 'period' instead of 'quarter'? NCB uses 'halves'.
    game = []
    quarter = 1
    end_of_quarter = False
    for play in plays:
        new_play = _play_as_dict(play)
        time = play[0]
        time_dict, quarter, end_of_quarter = _adjust_time(time,
                quarter, end_of_quarter, league)
        new_play.update(time_dict)
        try:
            scores = play[2]
        except IndexError:
            if len(game) > 0:
                # Official Play without score (new quarter, etc.)
                last_play = game[-1]
                new_play['away_score'] = last_play['away_score']
                new_play['home_score'] = last_play['home_score']
            else:
                # Start of game
                new_play['away_score'] = 0
                new_play['home_score'] = 0
        else:
            away_score, home_score = scores.split('-')
            new_play['away_score'] = int(away_score)
            new_play['home_score'] = int(home_score)
        game.append(new_play)
    return game


def _adjust_time(time, quarter, end_of_quarter, league):
    """
    Takes the time logic out of adjust_game.
    Returns a dict, quarter, and end_of_quarter.
    """
    new_time = re.split(':', time)
    minutes = int(new_time[0])
    seconds = int(new_time[1])
    if minutes is 0 and not end_of_quarter:
        end_of_quarter = True
    elif end_of_quarter and minutes > 1:
        quarter += 1
        end_of_quarter = False
    overall_time = _calc_overall_time(seconds, minutes, quarter, league)
    time_dict = {}
    time_dict['overall_time'] = overall_time
    time_dict['quarter_time'] = time
    time_dict['quarter'] = quarter
    return time_dict, quarter, end_of_quarter


def _league_time(league):
    """
    Return league specific game info -- number of quarters, regulation time
    limit, regular quarter length.
    """
    if league is 'nba':
        num_quarters = 4
        regulation_time = 48
        regular_quarter = 12
    else:
        num_quarters = 2
        regulation_time = 40
        regular_quarter = 20
    return num_quarters, regulation_time, regular_quarter


def _calc_overall_time(seconds, minutes, quarter, league):
    """
    Calculate the overall time that's elapsed for a given game. I'm not a fan
    of four arguments, but it's necessary unfortunately.
    """
    num_quarters, regulation_time, regular_quarter = _league_time(league)
    if quarter > num_quarters:
        # We're in overtime.
        quarter_length = 5
        overtimes = quarter - num_quarters
        previous_time = datetime.timedelta(minutes=(regulation_time +
            5 * (overtimes - 1)))
    else:
        quarter_length = regular_quarter
        previous_time = datetime.timedelta(minutes=(quarter_length *
            (quarter - 1)))
    mins = datetime.timedelta(minutes=quarter_length) -\
            datetime.timedelta(minutes=minutes, seconds=seconds)
    overall_time = str(mins + previous_time)
    return overall_time


def _play_as_dict(play):
    """
    Give it a play in list/tuple format, get back a dict containing
    official_play, home_play, and away_play data.

    Really only for internal use with adjust_game.
    """
    # TODO: Play can be '&nbsp;' or u'\xa0', so I put len < 10.
    # Should probably change to something more explicit in the future.
    new_play = {}
    import pdb; pdb.set_trace()
    if len(play) is 2:
        new_play['official_play'] = play[1]
        new_play['home_play'] = None
        new_play['away_play'] = None
    else:
        new_play['official_play'] = None
        away_play = play[1]
        home_play = play[3]
        if len(away_play) < 10:
            new_play['away_play'] = None
            new_play['home_play'] = home_play
        elif len(home_play) < 10:
            new_play['away_play'] = away_play
            new_play['home_play'] = None
    return new_play


def parse_team(row):
    """
    Return a mapping of play number to team
    """
    img = row.find('img')['src']
    team_regex = re.compile('500/(?P<team>.*)\.png')
    match = re.search(team_regex, img)
    team_name = match.group('team')
    return team_name


def to_seconds(quarter, timestamp):
    """
    Convert a quarter and time remaining to seconds since start of game.
    """
    seconds_in_quarter = 12 * 60
    total_seconds = seconds_in_quarter * (quarter - 1)

    minutes, seconds = timestamp.split(':')
    total_elapsed = total_seconds + seconds_in_quarter - (int(minutes) * 60) - int(seconds)
    return total_elapsed


def parse_plays(game_id):
    """Parse a game's Play-By-Play page on ESPN."""
    espn = 'http://scores.espn.com/nba/playbyplay?gameId={0}'.format(game_id)
    url = requests.get(espn)
    print url.url

    soup = bs(url.text, 'lxml')

    teams = defaultdict(lambda: defaultdict(list))

    for quarter in range(1, 5):
        table_id = 'gp-quarter-{0}'.format(quarter)
        table = soup.find('div', {'id': table_id}).find('table')
        thead = [thead.extract() for thead in table.findAll('thead')]
        all_rows = [tr for tr in table.findAll('tr')]

        for row in all_rows:
            team = parse_team(row)
            info = [tr.text for tr in row if tr(text=True)]

            if 'makes' in info[1]:
                seconds = to_seconds(quarter, info[0])
                play_info = [seconds, quarter] + info
                teams[team][seconds].append(play_info)

    return teams


def parse_play(play_strings):
    """
    Parse a list of string scoring descriptions into a dictionary
    """
    data = {}

    fts = [p for p in play_strings if 'free throw' in p[3]]
    non_fts = [p for p in play_strings if 'free throw' not in p[3]]
    assert len(non_fts) <= 1

    play = play_strings[0][3]
    player_regex = '(?P<player>.*) makes'
    data['player'] = re.search(player_regex, play).group('player')

    assist_regex = '\((?P<assist>.*) assists'
    assisted = re.search(assist_regex, play)
    if assisted:
        data['assist'] = assisted.group('assist')

    total_points = len(fts)
    if non_fts:
        play = non_fts[0][3]
        points = 3 if 'three' in play else 2
        total_points += points

    data['points'] = total_points
    return data


def persist(teams):

    play_data = defaultdict(list)
    for team in teams:
        for idx, ts in enumerate(sorted(teams[team].keys())):
            d = teams[team][ts]
            data = parse_play(d)
            data['timestamp'] = ts
            data['playNum'] = idx + 1
            data['quarter'] = d[0][1]
            data['time'] = d[0][2]
            play_data[team].append(data)

    with open('data/{0}.json'.format('-'.join(teams.keys())), 'w') as data_file:
        json.dump(play_data, data_file)


def get_games(day, league='nba', iterable=False):
    """
    Get the games and play-by-play data from ESPN for a date.
    The date can be in `datetime.date` format or be a YYYYMMDD string.

    By default it only looks for NBA games on a date. You can modify
    this by passing it a league='ncb' argument to scrape the NCAA men's
    basketball games that have Play-By-Play data (NOTE: not all will).

    You can pass it an optional `iterable=True` argument in order to receive
    back a generator instead of the default list.
    """
    espn_scoreboard = _format_scoreboard_url(day, league=league)
    all_games = scrape_links(espn_scoreboard)
    if not iterable:
        games = [parse_plays(game, league=league) for game in all_games]
    else:
        games =  (parse_plays(game, league=league) for game in all_games)
    return games


@click.command()
@click.option('--game')
def main(game):
    plays = parse_plays(game)
    persist(plays)


if __name__ == '__main__':
    main()
