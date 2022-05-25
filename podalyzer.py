#!/usr/bin/env python3

import subprocess
import podcastparser
import ffmpeg
import urllib.request
import tempfile
import json
import argparse
import os

# Parse command line arguments
def parseArgs():
	p = argparse.ArgumentParser(
		description="Output technical details of a podcast feed")
	p.add_argument('feedurl', help="URL of RSS feed")
	return p.parse_args()

# Generate a temporary file path and name
def genTempFile():
	tempdir = tempfile._get_default_tempdir()
	tempname = next(tempfile._get_candidate_names())
	return f"{tempdir}/podalyzer.{tempname}"


# Probe file with ffprobe, return audio stream info
def probeFile(f):
	probe = ffmpeg.probe(f)
	return next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)

# Run ffmpeg filter against file to return LUFS info
def getLufs(f):
	sp = subprocess.Popen(
		(
			ffmpeg
			.input(f"{f}")
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

def main(args):
	feedurl = args.feedurl
	parsed = podcastparser.parse(feedurl, urllib.request.urlopen(feedurl))

	title = parsed['title']
	latest_episode = parsed['episodes'][0]
	episode_title = latest_episode['title']
	episode_media = latest_episode['enclosures'][0]['url']

	file = genTempFile()
	print(f"Downloading to {file}")
	urllib.request.urlretrieve(episode_media, file)

	probeOut = probeFile(file)

	print("Analying LUFS...")
	lufsOut = getLufs(file)

	print(f"Title:    {title}")
	print(f"Episode:  {episode_title}")
	print(f"CODEC:    {probeOut['codec_name']}")
	print(f"Bit Rate: {probeOut['bit_rate']}")
	print(f"Samples:  {probeOut['sample_rate']}")
	print(f"Mode:     {probeOut['channel_layout']}")
	print(f"LUFS:    {lufsOut['input_i']}")
	print(f"Peak:    {lufsOut['input_tp']}")

	os.remove(file)

if __name__ == '__main__':
	main(parseArgs())

