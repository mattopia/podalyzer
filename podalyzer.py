#!/usr/bin/env python3

import subprocess
import podcastparser
import ffmpeg
import urllib.request
import tempfile
import json

# Parse command line arguments
def parseArgs():
	p = argparse.ArgumentParser(
		description="Output technical details of a podcast feed")
	p.add_argument('feedurl', help="URL of RSS feed")
	return p.parse_args()

# Probe file with ffprobe, return audio stream info
def probeFile(file):
	probe = ffmpeg.probe(file)
	return next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)

# Run ffmpeg filter against file to return LUFS info
def getLufs(file):
	sp = subprocess.Popen(
		(
			ffmpeg
			.input(f"{file}")
			.audio.filter("loudnorm", I=-16, TP=-1.5, LRA=11, print_format="json")
			.output("-", format="null")
			.global_args("-loglevel", "info")
			.global_args("-nostats")
			.global_args("-hide_banner")
			.compile()
		),
        	stderr=subprocess.PIPE
	)

	output = "\n".join(sp.communicate()[-1].decode("UTF-8").split("\n")[-13:-1])
	return json.loads(output)
	

if __name__ == '__main__':

	feedurl = 'https://feeds.megaphone.fm/20k'

	parsed = podcastparser.parse(feedurl, urllib.request.urlopen(feedurl))
	title = parsed['title']
	latest_episode = parsed['episodes'][0]
	episode_title = latest_episode['title']
	episode_media = latest_episode['enclosures'][0]['url']

	tempdir = tempfile._get_default_tempdir()
	tempname = next(tempfile._get_candidate_names())
	#tempfile = f"{tempdir}/{tempname}.mp3"
	tempfile = '/var/folders/9j/h2nw88l533s2fzs1241k741m0000gn/T/7ylfoe7n.mp3'
	#urllib.request.urlretrieve(episode_media, tempfile)

	probe = ffmpeg.probe(tempfile)
	audio_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)

	audio_stream = probeFile(tempfile)
	bit_rate = audio_stream['bit_rate']
	sample_rate = audio_stream['sample_rate']
	channel_layout = audio_stream['channel_layout']

	# broken LUFS stuff
	#audio_in = ffmpeg.input(tempfile).audio
	#af = audio_in.audio.filter('loudnorm', dualmono='true')
	lufsOut = getLufs(tempfile)
	import pprint
	pprint.pprint(lufsOut)

	print(f"Podcast Title: {title}")
	print(f"Episode Title: {episode_title}")
	print(f"Bit Rate:      {bit_rate}")
	print(f"Sample Rate:   {sample_rate}")
	print(f"Mode:          {channel_layout}")
