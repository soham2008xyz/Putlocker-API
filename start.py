from bs4 import BeautifulSoup
from util.decorators import crossdomain
from flask import Flask, url_for
import json
import lxml
import re
import urllib.request

# Base URLs
SHOWS_BASE = 'https://putlocker.fit/a-z-shows/'
SHOW_BASE = 'https://putlocker.fit/show/'

# Common config
user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
headers = { 'User-Agent' : user_agent }

# Bootstrap Flask server
app = Flask(__name__)

@app.route('/')
def hello_world():
	return 'Hello, World!'

@app.route('/show/')
@crossdomain(origin = '*')
def get_shows():
	request = urllib.request.Request(SHOWS_BASE, None, headers)
	with urllib.request.urlopen(request) as response:
		soup = BeautifulSoup(response.read().decode('utf-8'), 'lxml')
		groups = {}
		for table in soup.find_all('table', class_=re.compile('^lsl-')):
			title = table.find(class_=re.compile('^badge-info$')).string
			shows = []
			for show in table.find_all('a', class_=re.compile('^az_ls_ent$')):
				show_data = {}
				show_data['title'] = show.string
				url_parts = show['href'].split('/')
				show_data['url'] = url_for('get_show', show = url_parts[len(url_parts) - 2])
				shows.append(show_data)
			groups[title] = shows
	return json.dumps(groups)

@app.route('/show/<show>')
@crossdomain(origin = '*')
def get_show(show):
	request = urllib.request.Request(SHOW_BASE + show + '/', None, headers)
	with urllib.request.urlopen(request) as response:
		soup = BeautifulSoup(response.read().decode('utf-8'), 'lxml')
		seasons = {}
		for season in soup.select('h2 > a'):
			title = season.string
			episodes = []
			for episode in season.parent.find_next_sibling('table').find_all('a'):
				episode_data = {}
				title_parts = episode['title'].split(' - ')
				episode_data['title'] = episode.string + ((' - ' + title_parts[len(title_parts) - 1]) if title_parts[len(title_parts) - 1] else '' )
				url_parts = episode['href'].split('/')
				episode_data['season'] = url_parts[len(url_parts) - 3].split('-')[1]
				episode_data['episode'] = url_parts[len(url_parts) - 2].split('-')[1]
				episode_data['url'] = url_for('get_episode', show = show, season = url_parts[len(url_parts) - 3], episode = url_parts[len(url_parts) - 2])
				episodes.append(episode_data)
			seasons[title] = episodes
		show = {}
		nav_crumbs = soup.select('.breadcrumb-item')
		show['name'] = nav_crumbs[len(nav_crumbs) - 1].string
		show['image'] = soup.select('.thumb.pull-left > img')[0]['src']
		show['seasons'] = seasons
	return json.dumps(show)

@app.route('/show/<show>/<season>/<episode>')
@crossdomain(origin = '*')
def get_episode(show, season, episode):
	return show + ' - ' + season + ' - ' + episode