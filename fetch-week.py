from argparse import ArgumentParser
from collections import defaultdict
import pandas as pd
import requests


BASE_URL = 'https://stathead.com/football/play_finder.cgi?request=1&match=summary_all&sb=0&order_by=yards&year_min=2021&year_max=2021&game_type=R&game_num_min=0&game_num_max=99&minutes_max=15&seconds_max=0&minutes_min=0&seconds_min=0&field_pos_min_field=team&field_pos_max_field=team&end_field_pos_min_field=team&end_field_pos_max_field=team&no_play=N&type%5B%5D=PASS&type%5B%5D=RUSH'

def append_url_week(url, week):
	return url + '&week_num_min={}&week_num_max={}'.format(week, week)

def append_url_yards(url, yards_min, yards_max):
	return url + '&yards_min={}&yards_max={}'.format(yards_min, yards_max)

def append_url_no_turnover(url):
	return url + '&is_turnover=N'

def append_url_td(url):
	return url + '&is_turnover=N&is_scoring=Y&score_type%5B%5D=touchdown'

def append_first_down(url):
	return url + '&is_first_down=Y'

def week_urls(week):
	plays_url = append_url_week(BASE_URL, week)
	
	no_turnover_plays_url = append_url_no_turnover(plays_url)
	firsts_url = append_first_down(no_turnover_plays_url)
	twenties_url = append_url_yards(no_turnover_plays_url, 20, 39)
	forties_url = append_url_yards(no_turnover_plays_url, 40, 200)
	tds_url = append_url_td(no_turnover_plays_url)
	
	return {
		"plays": plays_url,
		"1st downs": firsts_url,
		"20-39": twenties_url,
		"40+": forties_url,
		"tds": tds_url,
	}


def add_slugging_to_week(teams_dict):
	for team_name, team_data in teams_dict.items():
		if team_data['plays'] > 0:
			team_data['on base'] = team_data['1st downs'] / float(team_data['plays'])
			team_data['slugging'] = (team_data['1st downs'] + 2*team_data['20-39'] + 3*team_data['40+'] + 4*team_data['tds']) / float(team_data['plays'])
			team_data['ops'] = team_data['on base'] + team_data['slugging']

def fetch_week(week):
	teams = defaultdict(lambda: defaultdict(lambda: 0))
	for name, url in week_urls(week).items():
		html = requests.get(url).content
		df_list = pd.read_html(html)
		table = df_list[2]
		
		assert(table.columns[0][1] == 'Tm')
		assert(table.columns[2][1] == 'Plays')
		
		for i, row in table.iterrows():
			teams[row.iloc[0]][name] = row.iloc[2]
	add_slugging_to_week(teams)
	return teams

def print_week(week):
	week_results = fetch_week(week)
	all_teams = sorted(list(week_results.keys()))
	for team in all_teams:
		team_data = week_results[team]
		print("{}: {} plays, {} 1sts, {} 20-39s, {} 40+s, {} TDs, {} on base, {} slugging, {} ops".format(
			team,
			team_data['plays'],
			team_data['1st downs'],
			team_data['20-39'],
			team_data['40+'],
			team_data['tds'],
			round(team_data['on base'], 4),
			round(team_data['slugging'], 4),
			round(team_data['ops'], 4),
		))



if __name__ == "__main__":
	parser = ArgumentParser(description='Fetch NFL slugging numbers for a week.')
	parser.add_argument('week', help='Which week do you want to calculate?')
	args = parser.parse_args()

	print_week(int(args.week))
