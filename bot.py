#!/usr/bin/env python

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import json
import requests
from datetime import datetime
from time import strftime, altzone, time
from math import floor

# YOU NEED TO ENTER A GOOGLE MAPS API CODE, A DISCORD CHANNEL ID WHICH THE BOT HAS PERMISSION TO TALK IN, AND DISCORD BOT TOKEN
googleapi = ''
defaultchannel = ''
bot_token = ''
bot_name = 'PoGoWebHookBot'
bot_url = 'http://some.site.com'
bot_version = '0.1'
pokesfile = 'pokes.json'

class S(BaseHTTPRequestHandler):
	
	def log_message(self, format, *args):
		return
		
	def do_POST(self):
		pokemon = self.get_incoming_pokemon_data()
		result = self.maybe_post_pokemon_to_discord(pokemon)
		try:
			self.send_response(200)
			self.send_header('Content-type', 'text/html')
			self.end_headers()
			self.wfile.write('<html><body>{}</body></html>'.format(result))
		except:
			pass
			
		#delete old messages from queue
		for idx, msg in enumerate(active_messages):
			if msg[0] < time():
				print 'deleting {} from {}'.format(msg[2],msg[1])
				print requests.delete('https://discordapp.com/api/v6/channels/{}/messages/{}'.format(msg[1],msg[2]),headers={'Authorization':'Bot {}'.format(bot_token),'User-Agent':'{} ({}, v{})'.format(bot_name,bot_url,bot_version)})
				active_messages.remove(msg)
		
	def get_incoming_pokemon_data(self):
		contentlength = int(self.headers['Content-Length'])
		jsonstring = self.rfile.read(contentlength)
		jsonobj = json.loads(jsonstring)
		return jsonobj['message']
	
	def maybe_post_pokemon_to_discord(self,pokemon):
		data = pokes[str(pokemon['pokemon_id'])]
		if data['ignore']:
			#print 'Found {} and {}'.format(data['name'],'doing nothing')
			return 'NO'
		data['remaining'] = round( floor( ( pokemon['disappear_time'] - time() ) / 60 ), 0 )
		if data['remaining'] < 1:
			#print 'Found {} and {}'.format(data['name'],'time is < 1 so doing nothing')
			return 'NO'
		message = self.build_message(pokemon,data)
		print message
		t_response = self.discord(message,'217877677200244736',False,pokemon['disappear_time'])
		v_response = self.discord(message,'217995047772225547',True,pokemon['disappear_time'])
		return 'YES'
					
	def build_message(self,pokemon,data):
		name = data['name']
		remaining = data['remaining']
		color = data['types'][0]['color']
		loc = '{},{}'.format(pokemon['latitude'],pokemon['longitude'])
		addr = self.get_address(loc)
		addrstring = self.build_addr_string(addr)
		timeformat = '%H:%M'
		despawntime = datetime.utcfromtimestamp( pokemon['disappear_time'] - altzone ).strftime(timeformat)
		url = 'https://www.google.com/maps/dir/Current+Location/{}'.format(loc,loc)
		return '{} is {} for {} more minutes until {} {}'.format(name,addrstring,int(remaining),despawntime,url)

	def discord(self, message, channel = defaultchannel,tts = False,delete_at=False):		
		response = requests.post('https://discordapp.com/api/v6/channels/{}/messages'.format(channel),headers={'Authorization':'Bot {}'.format(bot_token),'User-Agent':'{} ({}, v{})'.format(bot_name,bot_url,bot_version)},json={'content':message,'tts':tts}).json()
		if delete_at:
			active_messages.append([delete_at,channel,response['id']])
		
	def get_address(self,loc):
		geosearch = requests.get('https://maps.googleapis.com/maps/api/geocode/json?latlng={}&key={}'.format(loc,googleapi)).json()
		street_number = ''
		route = ''
		neighborhood = ''
		try:
			parts = geosearch['results'][0]['address_components']
			for part in parts:
				for type in part['types']:
					if type == 'street_number' and street_number == '':
						street_number = part['short_name']
					if type == 'route' and route == '':
						route = part['long_name']
					if type == 'neighborhood' and neighborhood == '':
						neighborhood = part['short_name']
		except:
			pass
		return [street_number,route,neighborhood]
	
	def build_addr_string(self,addr):
		if addr[2] == '':
			if addr[1] == '':
				addrstring = 'nearby'
			else:
				if addr[0] == '':
					addrstring = 'on {}'.format(addr[1])
				else:
					addrstring = 'at {} {}'.format(addr[0],addr[1])
		else:
			if addr[1] == '':
				addrstring = 'in {}'.format(addr[2])
			else:
				if addr[0] == '':
					addrstring = 'in {} on {}'.format(addr[2],addr[1])
				else:
					addrstring = 'in {} at {} {}'.format(addr[2],addr[0],addr[1])
		return addrstring;
		
if __name__ == "__main__":
	with open(pokesfile, 'r') as f:
		pokes = json.loads(f.read().decode('utf-8','ignore'))
	
	active_messages = []
		
	HTTPServer(('', 5151), S).serve_forever()
