from bs4 import BeautifulSoup
from flask import Flask, url_for
import json
import lxml
import re
import urllib.request

# Base URLs
SHOWS_BASE = 'https://putlocker.fit/a-z-shows/'

# Bootstrap Flask server
app = Flask(__name__)

@app.route('/')
def hello_world():
	return 'Hello, World!'

@app.route('/show/')
def get_shows():
	user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
	headers = { 'User-Agent' : user_agent }
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
def get_show(show):
	return show