#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
File:               gcexport.py
Original Author:    Kyle Krafka (https://github.com/kjkjava/)
Date:               April 28, 2015
Fork Author:        Johannes Heinrich (https://github.com/JohannesHeinrich/)
Date:               March 24, 2018
Description:        This script will export fitness data from Garmin Connect
                    See README.md for more detailed information
"""

from urllib import urlencode
from datetime import datetime
from getpass import getpass
from sys import argv
from os.path import isdir
from os.path import isfile
from os import mkdir
from os import remove
from xml.dom.minidom import parseString
from subprocess import call

import urllib, urllib2, cookielib, json
from fileinput import filename

import argparse
import zipfile

script_version = '1.0.0'
current_date = datetime.now().strftime('%Y-%m-%d')
activities_directory = './' + current_date + '_garmin_connect_export'

parser = argparse.ArgumentParser()

parser.add_argument('--version', help="print version and exit", action="store_true")
parser.add_argument('--username', help="your Garmin Connect username (otherwise, you will be prompted)", nargs='?')
parser.add_argument('--password', help="your Garmin Connect password (otherwise, you will be prompted)", nargs='?')

parser.add_argument('-c', '--count', nargs='?', default="1",
	help="number of recent activities to download, or 'all' (default: 1)")

parser.add_argument('-f', '--format', nargs='?', choices=['gpx', 'tcx', 'original'], default="gpx",
	help="export format; can be 'gpx', 'tcx', or 'original' (default: 'gpx')")

parser.add_argument('-d', '--directory', nargs='?', default=activities_directory,
	help="the directory to export to (default: './YYYY-MM-DD_garmin_connect_export')")

parser.add_argument('-u', '--unzip',
	help="if downloading ZIP files (format: 'original'), unzip the file and removes the ZIP file",
	action="store_true")

args = parser.parse_args()

if args.version:
	print argv[0] + ", version " + script_version
	exit(0)

cookie_jar = cookielib.CookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar))
# print cookie_jar

# url is a string, post is a dictionary of POST parameters, headers is a dictionary of headers.
def http_req(url, post=None, headers={}):
	request = urllib2.Request(url)
	# request.add_header('User-Agent', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/1337 Safari/537.36')  # Tell Garmin we're some supported browser.
	request.add_header('User-Agent', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2816.0 Safari/537.36')  # Tell Garmin we're some supported browser.
	for header_key, header_value in headers.iteritems():
		request.add_header(header_key, header_value)
	if post:
		# print "POSTING"
		post = urlencode(post)  # Convert dictionary to POST parameter string.
	# print request.headers
	# print cookie_jar
	# print post
	# print request
	response = opener.open(request, data=post)  # This line may throw a urllib2.HTTPError.

	# N.B. urllib2 will follow any 302 redirects. Also, the "open" call above may throw a urllib2.HTTPError which is checked for below.
	# print response.getcode()
	if response.getcode() != 200:
		raise Exception('Bad return code (' + str(response.getcode()) + ') for: ' + url)

	return response.read()

print 'Welcome to Garmin Connect Exporter!'

# Create directory for data files.
if isdir(args.directory):
	print 'Warning: Output directory already exists. Already downloaded files will be skipped.'

username = args.username if args.username else raw_input('Username: ')
password = args.password if args.password else getpass()

# Maximum number of activities you can request at once.  Set and enforced by Garmin.
limit_maximum = 100

hostname_url = http_req('http://connect.garmin.com/gauth/hostname')
# print hostname_url
hostname = json.loads(hostname_url)['host']

REDIRECT = "https://connect.garmin.com/post-auth/login"
BASE_URL = "http://connect.garmin.com/en-US/signin"
GAUTH = "http://connect.garmin.com/gauth/hostname"
SSO = "https://sso.garmin.com/sso"
CSS = "https://static.garmincdn.com/com.garmin.connect/ui/css/gauth-custom-v1.1-min.css"

data = {'service': REDIRECT,
    'webhost': hostname,
    'source': BASE_URL,
    'redirectAfterAccountLoginUrl': REDIRECT,
    'redirectAfterAccountCreationUrl': REDIRECT,
    'gauthHost': SSO,
    'locale': 'en_US',
    'id': 'gauth-widget',
    'cssUrl': CSS,
    'clientId': 'GarminConnect',
    'rememberMeShown': 'true',
    'rememberMeChecked': 'false',
    'createAccountShown': 'true',
    'openCreateAccount': 'false',
    'usernameShown': 'false',
    'displayNameShown': 'false',
    'consumeServiceTicket': 'false',
    'initialFocus': 'true',
    'embedWidget': 'false',
    'generateExtraServiceTicket': 'false'}

print urllib.urlencode(data)

# URLs for various services.
url_gc_login     = 'https://sso.garmin.com/sso/login?' + urllib.urlencode(data)
url_gc_post_auth = 'https://connect.garmin.com/post-auth/login?'
url_gc_search    = 'http://connect.garmin.com/proxy/activity-search-service-1.2/json/activities?'
url_gc_gpx_activity = 'https://connect.garmin.com/modern/proxy/download-service/export/gpx/activity/'
url_gc_tcx_activity = 'https://connect.garmin.com/modern/proxy/download-service/export/tcx/activity/'
url_gc_original_activity = 'http://connect.garmin.com/proxy/download-service/files/activity/'
# url_gc_login     = 'https://sso.garmin.com/sso/login?service=https%3A%2F%2Fconnect.garmin.com%2Fpost-auth%2Flogin&webhost=olaxpw-connect04&source=https%3A%2F%2Fconnect.garmin.com%2Fen-US%2Fsignin&redirectAfterAccountLoginUrl=https%3A%2F%2Fconnect.garmin.com%2Fpost-auth%2Flogin&redirectAfterAccountCreationUrl=https%3A%2F%2Fconnect.garmin.com%2Fpost-auth%2Flogin&gauthHost=https%3A%2F%2Fsso.garmin.com%2Fsso&locale=en_US&id=gauth-widget&cssUrl=https%3A%2F%2Fstatic.garmincdn.com%2Fcom.garmin.connect%2Fui%2Fcss%2Fgauth-custom-v1.1-min.css&clientId=GarminConnect&rememberMeShown=true&rememberMeChecked=false&createAccountShown=true&openCreateAccount=false&usernameShown=false&displayNameShown=false&consumeServiceTicket=false&initialFocus=true&embedWidget=false&generateExtraServiceTicket=false'
# url_gc_search    = 'http://connect.garmin.com/proxy/activity-search-service-1.0/json/activities?'
# url_gc_gpx_activity = 'http://connect.garmin.com/proxy/activity-service-1.2/gpx/activity/'
# url_gc_tcx_activity = 'http://connect.garmin.com/proxy/activity-service-1.2/tcx/activity/'

# Request a valid session cookie, pulling the login page
print 'Request login page'
http_req(url_gc_login)
print 'Finish login page'

# Login
post_data = {'username': username, 'password': password, 'embed': 'true', 'lt': 'e1s1', '_eventId': 'submit', 'displayNameRequired': 'false'}
# Fields that are passed in a typical Garmin login.
print 'Post login data'
http_req(url_gc_login, post_data)
print 'Finish login post'
# Get the key.
login_ticket = None
print "COOKIE"
for cookie in cookie_jar:
	print cookie.name + ": " + cookie.value
	if cookie.name == 'CASTGC':
		login_ticket = cookie.value
		print login_ticket
		print cookie.value
		break
print "COOKIE"

if not login_ticket:
	raise Exception('Did not get a ticket cookie. Cannot log in. Did you enter the correct username and password?')

# Chop of 'TGT-' off the beginning, prepend 'ST-0'.
login_ticket = 'ST-0' + login_ticket[4:]
# print login_ticket

print 'Request authentication'
# print url_gc_post_auth + 'ticket=' + login_ticket
http_req(url_gc_post_auth + 'ticket=' + login_ticket)
print 'Finished authentication'
print "Call modern"
http_req("http://connect.garmin.com/modern")
print "Finish modern"
print "Call legacy session"
http_req("https://connect.garmin.com/legacy/session")
print "Finish legacy session"

# Logged in
if not isdir(args.directory):
	mkdir(args.directory)

# Downloading files from Garmin Connect
download_all = False
if args.count == 'all':
	# If the user wants to download all activities, first download one,
	# then the result of that request will tell us how many are available
	# so we will modify the variables then.
	total_to_download = 1
	download_all = True
else:
	total_to_download = int(args.count)
total_downloaded = 0

# This while loop will download data from the server in multiple chunks, if necessary.
while total_downloaded < total_to_download:
	# Maximum of 100... 400 return status if over 100.  So download 100 or whatever remains if less than 100.
	if total_to_download - total_downloaded > 100:
		num_to_download = 100
	else:
		num_to_download = total_to_download - total_downloaded

	search_params = {'start': total_downloaded, 'limit': num_to_download}
	# Query Garmin Connect
	print url_gc_search + urlencode(search_params)
	result = http_req(url_gc_search + urlencode(search_params))
	
	# Persist JSON
	json_filename = args.directory + '/activities.json'
	json_file = open(json_filename, 'a')
	json_file.write(result)
	json_file.close()

	json_results = json.loads(result)  # TODO: Catch possible exceptions here.

	# search = json_results['results']['search']

	if download_all:
		# Modify total_to_download based on how many activities the server reports.
		total_to_download = int(json_results['results']['totalFound'])

		# Do it only once.
		download_all = False

	# Pull out just the list of activities.
	activities = json_results['results']['activities']

	# Process each activity.
	for a in activities:
		# Display which entry we're working on.
		print '[' + str(a['activity']['activityId']) + ']'
		if args.format == 'gpx':
			data_filename = args.directory + '/activity_' + str(a['activity']['activityId']) + '.gpx'
			download_url = url_gc_gpx_activity + str(a['activity']['activityId']) + '?full=true'
			# download_url = url_gc_gpx_activity + str(a['activity']['activityId']) + '?full=true' + '&original=true'
			print download_url
			file_mode = 'w'
		elif args.format == 'tcx':
			data_filename = args.directory + '/activity_' + str(a['activity']['activityId']) + '.tcx'
			download_url = url_gc_tcx_activity + str(a['activity']['activityId']) + '?full=true'
			file_mode = 'w'
		elif args.format == 'original':
			data_filename = args.directory + '/activity_' + str(a['activity']['activityId']) + '.zip'
			fit_filename = args.directory + '/' + str(a['activity']['activityId']) + '.fit'
			download_url = url_gc_original_activity + str(a['activity']['activityId'])
			file_mode = 'wb'
		else:
			raise Exception('Unrecognized format.')

		if isfile(data_filename):
			print 'Data file already exists; skipping...'
			continue
		if args.format == 'original' and isfile(fit_filename):  # Regardless of unzip setting, don't redownload if the ZIP or FIT file exists.
			print 'FIT data file already exists; skipping...'
			continue

		# Download the data file from Garmin Connect.
		# If the download fails (e.g., due to timeout), this script will die, but nothing
		# will have been written to disk about this activity, so just running it again
		# should pick up where it left off.
		print 'Downloading...',

		try:
			data = http_req(download_url)
		except urllib2.HTTPError as e:
			# Handle expected (though unfortunate) error codes; die on unexpected ones.
			if e.code == 500 and args.format == 'tcx':
				# Garmin will give an internal server error (HTTP 500) when downloading TCX files if the original was a manual GPX upload.
				# Writing an empty file prevents this file from being redownloaded, similar to the way GPX files are saved even when there are no tracks.
				# One could be generated here, but that's a bit much. Use the GPX format if you want actual data in every file,
				# as I believe Garmin provides a GPX file for every activity.
				print 'Writing empty file since Garmin did not generate a TCX file for this activity...',
				data = ''
			elif e.code == 404 and args.format == 'original':
				# For manual activities (i.e., entered in online without a file upload), there is no original file.
				# Write an empty file to prevent redownloading it.
				print 'Writing empty file since there was no original activity data...',
				data = ''
			else:
				raise Exception('Failed. Got an unexpected HTTP error (' + str(e.code) + ').')

		save_file = open(data_filename, file_mode)
		save_file.write(data)
		save_file.close()

		if args.format == 'gpx':
			# Validate GPX data. If we have an activity without GPS data (e.g., running on a treadmill),
			# Garmin Connect still kicks out a GPX, but there is only activity information, no GPS data.
			# N.B. You can omit the XML parse (and the associated log messages) to speed things up.
			gpx = parseString(data)
			gpx_data_exists = len(gpx.getElementsByTagName('trkpt')) > 0

			if gpx_data_exists:
				print 'Done. GPX data saved.'
			else:
				print 'Done. No track points found.'
		elif args.format == 'original':
			if args.unzip and data_filename[-3:].lower() == 'zip':  # Even manual upload of a GPX file is zipped, but we'll validate the extension.
				print "Unzipping and removing zip files...",
				zip_file = open(data_filename, 'rb')
				z = zipfile.ZipFile(zip_file)
				for name in z.namelist():
					z.extract(name, args.directory)
				zip_file.close()
				remove(data_filename)
			print 'Done.'
		else:
			print 'Done.'
	total_downloaded += num_to_download
# End while loop for multiple chunks.

print 'Done!'
