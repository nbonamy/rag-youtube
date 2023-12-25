import os
import re
import tempfile
from yt_dlp import YoutubeDL

class Downloader:

  def get_info(self, url):
    ydl_opts = {
      'verbose': False,
      'quiet': True,
    }
    with YoutubeDL(ydl_opts) as ydl:
      return ydl.extract_info(url, download=False)

  def download_captions(self, url, lang=None):
    captions_filename = self._download_captions(url, lang)
    original_captions = open(captions_filename, 'r').read()
    os.remove(captions_filename)
    return original_captions

  def prepare_captions(self, info, original_captions):
    captions = self._cleanup_captions(original_captions)
    # captions = f'{info["snippet"]["title"]} {captions}'
    return captions

  def _download_captions(self, url, lang=None):

    # get temp directory with system call
    tmp_dir = tempfile.gettempdir()

    # default lang
    if lang is None or lang == '':
      lang = 'en'

    # basic options
    ydl_opts = {
      'verbose': False,
      'skip_download': True,
      'writesubtitles': True,
      'writeautomaticsub': True,
      'subtitleslangs': [lang],
      'outtmpl': f'{tmp_dir}/%(id)s.%(ext)s',
    }

    # extract video id
    video_id = url if '=' not in url else url.split('=')[1]

    # download captions
    with YoutubeDL(ydl_opts) as ydl:
      ydl.download(url)
      return f'{tmp_dir}/{video_id}.{lang}.vtt'

  def _cleanup_captions(self, original_captions):

    # copy
    contents = original_captions

    # remove header lines
    contents = re.sub(r'WEBVTT\n', '', contents)
    contents = re.sub(r'Kind: captions\n', '', contents)
    contents = re.sub(r'Language: en\n', '', contents)

    # remove timestamp lines
    contents = re.sub(r'\d\d:\d\d:\d\d\.\d\d\d --> .*\n', '', contents)
    
    # now remove timestamps like <00:20:03.039><c>
    contents = re.sub(r'<\d\d:\d\d:\d\d\.\d\d\d><c>', '', contents)
    contents = re.sub(r'</c>', '', contents)
    contents = re.sub(r'\n+', '\n', contents)

    # now remove music
    contents = re.sub(r'\[Music\]', '', contents)

    # now combine lines
    captions = ''
    previous_line = ''
    for line in contents.split('\n'):
      line = line.strip()
      if line != '' and previous_line != line:
        captions += line + ' '
        previous_line = line
    
    # done
    return captions

