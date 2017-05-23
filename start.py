from bs4 import BeautifulSoup
from util.decorators import crossdomain
from flask import Flask, url_for
import json
import lxml
import re
import requests
import urllib.request

# Base URLs
SHOWS_BASE = 'https://putlocker.fit/a-z-shows/'
SHOW_BASE = 'https://putlocker.fit/show/'
API_BASE = 'https://putlocker.fit/wp-admin/admin-ajax.php'

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
	request = urllib.request.Request(SHOW_BASE + show + '/' + season + '/' + episode + '/', None, headers)
	with urllib.request.urlopen(request) as response:
		soup = BeautifulSoup(response.read().decode('utf-8'), 'lxml')
		jsondata = json.loads(soup.find(inline_script).string.split(' = ')[1].split(';')[0])
		postdata = {
			'action': 'get_src',
			'data': jsondata['id_token'],
			'post_id': jsondata['postid'],
			'e': jsondata['eid'],
			'm': jsondata['mid']
		}
		r = requests.post(url = API_BASE, data = postdata)
		postdata = {
			'action': 'get_playlist',
			'e': jsondata['eid'],
			'x': r.text.split(', ')[0].split('\'')[1],
			'y': r.text.split(', ')[1].split('\'')[1]
		}
		r2 = requests.post(url = API_BASE, data = postdata)
		videodata = json.loads(r2.text)
		video = {}
		video['image'] = jsondata['poster']
		video['tracks'] = videodata['tracks']
		video['sources'] = videodata['sources']
	return json.dumps(video)

# Utility functions
def inline_script(tag):
	return tag.name == 'script' and not tag.has_attr('src')