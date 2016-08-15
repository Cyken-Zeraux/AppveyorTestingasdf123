#!/usr/bin/env python3
import urllib.request
import json
import io
import decimal
import pprint
import subprocess
import re
import os
from tqdm import tqdm
import requests
import sys

def getspotifybuilds(versionfileloc):

	#open up cefglue versioning file
	with open(versionfileloc, 'r') as versionfile:
		data = versionfile.read()

	#Get CEF_VERSION with regex for now
	cef_version_pattern = re.compile( r'public\s+const\s+string\s+CEF_VERSION\s+=\s"(\d+\.\d+\.\d+\.\S+)";', re.IGNORECASE)

	version_search = cef_version_pattern.search(data)
	if version_search == None:
		raise ValueError("Couldn't find CEF_VERSION, aborting")

	#Actual cef_version from capture group
	CEF_VERSION = version_search.group(1)
	
	print("Querying spotify CEF builds list to match with Cefglue version")
	spotify_builds_index_raw = urllib.request.urlopen(r'http://opensource.spotify.com/cefbuilds/index.json').read().decode('utf-8')
	
	spotify_builds_object = json.loads(spotify_builds_index_raw)
	spotify_x86_client_download_object = {}
	#iterate over objects, build URL for CEF test client
	for version in spotify_builds_object["windows32"]["versions"]:
		if version["cef_version"] == CEF_VERSION:
			for build in version["files"]:
				if build["type"] == "client":
					spotify_x86_client_download_object['chromium_version'] = version['chromium_version']
					spotify_x86_client_download_object['url'] = r'http://opensource.spotify.com/cefbuilds/' + build["name"]
					spotify_x86_client_download_object['name'] = build["name"]
		
	if not spotify_x86_client_download_object['url'] or not spotify_x86_client_download_object['name']:
		raise ValueError("Couldn't match cefglue x86 version to spotify cef build")

	spotify_x64_client_download_object = {}
	for version in spotify_builds_object["windows64"]["versions"]:
		if version["cef_version"] == CEF_VERSION:
			for build in version["files"]:
				if build["type"] == "client":
					spotify_x64_client_download_object['chromium_version'] = version['chromium_version']
					spotify_x64_client_download_object['url'] = r'http://opensource.spotify.com/cefbuilds/' + build["name"]
					spotify_x64_client_download_object['name'] = build["name"]
		
	if not spotify_x64_client_download_object['url'] or not spotify_x64_client_download_object['name']:
		raise ValueError("Couldn't match cefglue x64 version to spotify cef build")

	if spotify_x86_client_download_object['chromium_version'] != spotify_x64_client_download_object['chromium_version']:
		raise ValueError("x86 and x64 spotify cef builds are not the same version of chromium")
		
	return {"cef_version": version_search, "chromium_version": spotify_x86_client_download_object['chromium_version'], "x86": spotify_x86_client_download_object, "x64": spotify_x64_client_download_object}

	
def main(argv):
	spotify_dict = {}
	for arg in argv:
		if arg == "checkupdate":
			spotify_dict = getspotifybuilds('CefGlue/Interop/version.g.cs')
		elif arg == "downloadupdate":
			if not spotify_dict:
				spotify_dict = getspotifybuilds('CefGlue/Interop/version.g.cs')
				
			response = requests.get(spotify_dict['x86']['url'], stream=True)

			with open(spotify_dict['x86']['name'], "wb") as handle:
				total_length = int(response.headers.get('content-length'))
				print("Downloading: " + spotify_dict['x86']['url'])
				for data in tqdm(iterable=response.iter_content(), unit="B", unit_scale='kilo', total=(total_length) + 1):
					handle.write(data)

			response = requests.get(spotify_dict['x64']['url'], stream=True)

			with open(spotify_dict['x64']['name'], "wb") as handle:
				total_length = int(response.headers.get('content-length'))
				print("Downloading: " + spotify_dict['x64']['url'])
				for data in tqdm(iterable=response.iter_content(), unit="B", unit_scale='kilo', total=(total_length) + 1):
					handle.write(data)
			
if __name__ == "__main__":
	main(sys.argv[1:])

