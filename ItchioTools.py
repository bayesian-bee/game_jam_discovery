from bs4 import BeautifulSoup
import requests
import time
import json

# scrapes games from itchio game jams
class ItchioScraper:

	def __init__(self, sleep_timer=0.1):
		self.game_jam_page = 'https://itch.io/jams/past/with-participants?page='
		self.base_itchio_url = 'https://itch.io'
		self.default_results_suffix = '/results?page='
		self.sleep_timer = sleep_timer

	def parse_int(num_string):
		if('k' in num_string):
			return int(float(num_string.split("k")[0])*1000)
		elif(',' in num_string):
			return int(num_string.replace(',',''))
		else:
			return int(num_string)
    
	def sleepy_get_page(self, page_ind):
		time.sleep(self.sleep_timer)
		return requests.get(self.game_jam_page+str(page_ind))

	def scrape_jam_urls(self):
		soup = BeautifulSoup(self.sleepy_get_page(1).text, features="lxml")
		max_pages = int(soup.find("span", {'class':'pager_label'}).find("a").text)
		data = []
		for i in range(1, max_pages):
			url = self.game_jam_page + str(i)
			print('Getting page %d / %d...' % (i, max_pages))
			response = self.sleepy_get_page(i)
			soup = BeautifulSoup(response.text, features="lxml")
			jams = soup.find_all("div", {"class": "jam lazy_images"})
			for j in jams:
				jam_url = self.base_itchio_url + j.find("div", {"class": "primary_info"}).find("a")['href']
				stats = j.find("div", {"class": "jam_stats"}).find_all("span", {"class": "number"})
				participants = ItchioScraper.parse_int(stats[0].text)
				try:
					submissions = ItchioScraper.parse_int(stats[1].text)
				except:
					submissions = 0
				host = j.find("div", {"class": "hosted_by meta_row"}).find("a")['href']
				data.append({
					'jam_url':jam_url,
					'participants':participants,
					'submissions':submissions,
					'host':host,
				})
		print('Done scraping!')
		return data

	def get_games_from_jams(self, jams):
		game_data = []
		invalid_jams = []
		start_time = time.time()
		for i in range(0, len(jams)):
			stop_time = time.time()
			print('Scraping jam %d / %d... (prev: %0.2f sec)' % (i, len(jams), (stop_time - start_time)))
			print(jams[i]['jam_url'])
			start_time = time.time()
			if(jams[i]['submissions']>0):
				jam_data, has_results = self.scrape_jam(jams[i])
				game_data += jam_data
				if(not has_results):
					invalid_jams.append(jams[i])

		return game_data, invalid_jams

	def scrape_jam(self,jam):
		time.sleep(self.sleep_timer)
		soup = BeautifulSoup(requests.get(jam['jam_url']+self.default_results_suffix+"1").text, features="lxml")
		if(soup.find("a",{'class':'header_tab active'}) == None):
			print('---%s is not a valid jam!' % jam['jam_url'])
			return ([], False)
		elif(soup.find("a",{'class':'header_tab active'}).text.lower() == 'results'):
			print('---Scraping results')
			return (self.scrape_results(jam, soup), True)
		else:
			print('---Scraping submissions')
			return (self.scrape_submissions(jam, soup), False)

	#TODO(bee): Build this !!!
	def scrape_submissions(self, jam, soup):
		return []

	def scrape_results(self, jam, soup):
		active_header = soup.find("a",{'class':'nav_btn active'})
		if(active_header == None):
			results_suffix = self.default_results_suffix
		elif(active_header.text.lower() != 'overall'):
			results_suffix = "results/overall?page=1"
		else:
			results_suffix = self.default_results_suffix
		try:
			max_pages = int(soup.find("span",{'class':'pager_label'}).find('a').text)
		except:
			max_pages = 1

		jam_data = []
		for i in range(0, max_pages):
			time.sleep(self.sleep_timer)
			soup = BeautifulSoup(requests.get(jam['jam_url']+results_suffix+str(i+1)).text, features="lxml")
			games = soup.find_all("div",{'class':"game_summary"})
			for g in games:
				rank = g.find('strong',{'class':'ordinal_rank'}).text
				url = g.find('a')['href']
				name = g.find('a').text
				jam_data.append({
					'game_name':name,
					'game_url':url,
					'game_rank':rank,
					**jam
				})
		return jam_data

class ItchioDataManager:

	def __init__(self, jam_fname, game_fname, invalid_fname):
		self.jam_fname = jam_fname
		self.game_fname = game_fname
		self.invalid_fname = invalid_fname

		self.jam_data = self.load_jam_data()
		self.game_data = self.load_game_data()
		self.invalid_jams = self.load_invalid_data()

		self.offset = self.determine_offset()

	def load_jam_data(self):
		try:
			with open(self.jam_fname, 'r') as f:
				return json.load(f)
		except FileNotFoundError:
			print('%s not found!' % self.jam_fname)
			return []

	def load_game_data(self):
		try:
			with open(self.game_fname, 'r') as f:
				return json.load(f)
		except FileNotFoundError:
			print('%s not found!' % self.game_fname)
			return []

	def load_invalid_data(self):
		try:
			with open(self.invalid_fname, 'r') as f:
				return json.load(f)
		except FileNotFoundError:
			print('%s not found!' % self.invalid_fname)
			return []

	def save_game_data(self):
		with open(self.game_fname, 'w') as f:
			json.dump(self.game_data, f, indent=4)

	def save_invalid_data(self):
		with open(self.invalid_fname, 'w') as f:
			json.dump(self.invalid_jams, f, indent=4)

	def determine_offset(self):
		if(len(self.game_data)==0):
			print('No games scraped, starting at 0...')
			return 0

		most_recent_jam_scraped = self.game_data[-1]['jam_url']
		for i in range(0, len(self.jam_data)):
			if self.jam_data[i]['jam_url'] == most_recent_jam_scraped:
				return i+1

		print('Offset not found! Using 0...')
		return 0

	def get_games_from_jams(self, backup_interval=10):
		scraper = ItchioScraper()
		i = self.offset
		while(i < len(self.jam_data)):
			jam_buffer = []
			for j in range(0, backup_interval):
				if(i >= len(self.jam_data)):
					break
				jam_buffer.append(self.jam_data[i])
				i += 1
			games, invalid = scraper.get_games_from_jams(jam_buffer)
			self.game_data += games
			self.invalid_jams += invalid
			print('Saving....')
			self.save_game_data()
			self.save_invalid_data()

		print('Done!! Saving...')
		self.save_game_data()
		self.save_invalid_data()

if(__name__ == "__main__"):
	jam_fname = 'jam_metadata.json'
	game_fname = 'game_data.json'
	invalid_fname = 'invalid_jams.json'
	data_manager = ItchioDataManager(jam_fname, game_fname, invalid_fname)

	data_manager.get_games_from_jams()