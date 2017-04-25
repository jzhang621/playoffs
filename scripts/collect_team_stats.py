from collections import defaultdict

from bs4 import BeautifulSoup, Comment
import requests

from models.teams import Team
from models.stats import Stats

GAMES_IN_SEASON = 82.0

url = 'http://www.basketball-reference.com/leagues/NBA_{0}.html'


def get_team_stats_html(season):
    """
    Get the HTML for the given season.

    :param int season: The season to get data for.
    :return: String HTML data.
    """
    stats_url = url.format(season)
    stats_page = requests.get(stats_url).text
    return stats_page


def comment_to_table_rows(html_scraper, table_id):
    """
    Convert a commented html table with the given table_id into a list of rows

    :param html_scraper: BeautifulSoup object.
    :return: A list of rows containing data to be scraped.
    """
    comments = html_scraper.find(string=lambda text: isinstance(text, Comment) and table_id in text)
    scraped_comments = BeautifulSoup(comments, 'lxml')
    table = scraped_comments.find('table', {'id': table_id}).find('tbody')
    rows = table.findAll('tr')
    return rows


def scrape_team_stats(html):
    """
    Scrape a season HTML page into a dictionary with relevant data extracted.

    :param str html: The data to scrape.
    :return: A dictionary mapping team_name to a dictionary of relevant data.
    """
    scraper = BeautifulSoup(html, 'lxml')
    data_by_team = {}

    team_ratings = comment_to_table_rows(scraper, 'misc_stats')
    for team in team_ratings:
        data = _scrape_team_ratings(team)
        data_by_team.update(data)

    team_stats = comment_to_table_rows(scraper, 'team-stats-base')
    opp_stats = comment_to_table_rows(scraper, 'opponent-stats-base')
    pt_diff_by_team = scrape_pt_diff(team_stats, opp_stats)
    for team, pt_diff in pt_diff_by_team.iteritems():
        data_by_team[team].update(pt_diff)

    return data_by_team


def scrape_pt_diff(team_stats, opp_stats):
    """
    Scrape the point differential for each team.

    :param list team_stats: A list of rows containing points scored data for each team.
    :param list opp_stats: A list of rows containing points against data for each team.
    :return: A dictionary mapping team name to a point differential.
    """
    points_data_by_team = defaultdict(dict)
    for team in team_stats:
        team_data = scrape_team_point_data(team, 'points_scored')
        points_data_by_team[team_data['name']].update(team_data)

    for team in opp_stats:
        team_data = scrape_team_point_data(team, 'points_against')
        points_data_by_team[team_data['name']].update(team_data)

    pt_diff_by_team = {}
    for team, data in points_data_by_team.iteritems():
        pt_diff = data['points_scored'] - data['points_against']
        pt_diff_by_team[team] = {'pt_diff': round(pt_diff / GAMES_IN_SEASON, 1)}

    return pt_diff_by_team


def scrape_team_point_data(team_data, point_type):
    """
    Scrape team_point data of the given type.

    :param list team_data: A list of rows containing points data for each team.
    :param str point_type: The type of point data (i.e. 'points_scored', 'points_against')
    :return: A dictionary mapping team name to point data.
    """
    columns = team_data.findAll('td')
    team_name = _extract_team_name_from_columns(columns)
    points = int(columns[-1].text)
    return {'name': team_name, point_type: points}


def _scrape_team_ratings(team):
    """
    Scrape a team's offensive and defensive ratings and pace.

    :param team: A group of html elements.
    :return: A dictionary mapping team name to a dictionary of data.
    """
    columns = team.findAll('td')

    team_name = _extract_team_name_from_columns(columns)
    team_data = {
        team_name: {
            'off_rtg': float(columns[9].text),
            'def_rtg': float(columns[10].text),
            'pace': float(columns[11].text)
        }
    }
    return team_data


def _extract_team_name_from_columns(columns):
    """
    Extract a team name from a list of columns.

    :param list columns: A list of columns.
    :return: A team name
    """
    return columns[0].find('a', href=True)['href'].split('/')[2]


def scrape():
    """
    Scrape team stats for the given seasons.
    """
    for season in [2013, 2014, 2015, 2016]:
        print 'getting season data for {0}'.format(season)
        html = get_team_stats_html(season)
        data_by_team = scrape_team_stats(html)
        for team_name, data in data_by_team.iteritems():
            team = Team.get_or_create(team_name)

            data['season'] = int(season)
            data['team_id'] = team.id
            stats = Stats(**data)
            Stats.add(stats)


if __name__ == '__main__':
    scrape()
