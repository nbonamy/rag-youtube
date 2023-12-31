
import time
import json

def now():
  return time.time() * 1000
  
def get_video_info(video_id):
  with open('videos.json') as f:
    videos = json.load(f)
    for video in videos:
      if video['id']['videoId'] == video_id:
        return video
    return None

def get_video_url(video_id):
  return f'https://www.youtube.com/watch?v={video_id}'

def dumpj(data, filename):
  with open(filename, 'w') as f:
    f.write(json.dumps(data, indent=2))
