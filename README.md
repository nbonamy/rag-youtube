# rag-youtube

A set of scripts to build a RAG from the videos of a YouTube channel.

## Prerequisites

YouTube Data API: You need a Google Cloud account and a project set up in the Google Developer Console. Enable the YouTube Data API for your project and get an API key.

Get the video ID of any of the videos of the channel you want to analyze. You can extract this directly from the URL. For instance in `https://www.youtube.com/watch?v=AS2m2rRn9Cw&t=211s` the video ID is `AS2m2rRn9Cw`.

You also need [Ollama](https://ollama.ai) installed with one model installed. Mistral or LLama2 are preferred.

## Setup

```
pip install -r requirements.txt
```

## Preparation

We will execute the following steps:

- Get the list of all videos of the channel
- Download subtitles/captions for each video
- Load the subtitles/captions in our embedding database

Once this is done, you can run the web interface and ask questions to the channel host!

### List all videos

```
GOOGLE_API_KEY=XXXX ./src/list_videos.py AS2m2rRn9Cw
```

Of course, replace `XXXX` and `AS2m2rRn9Cw` with your own values. This will create a file called `videos.json` with all the information.

### Download the subtitles/captions

```
./src/download_captions.py
```

This will create a folder `captions` and download two files for each video:
- `<id>.original.vtt`: original subtitles/captions
- `<id>.cleaned.vtt`: processed subtitles/captions (timestamps removed)

Note that if the original captions already exist, they will not be downloaded again. Existing files will be processed again to recalculate cleaned versions (useful in case of rag-youtube upgrade).

### Load in the database

```
./src/document_loader.py
```

This will load all documents and create a file called `loaded.json` with the files correctly processed. This way, you can re-run the script if you downloaded new subtitles and just add the new ones to the database.

To start over, simply delete the `db` folder and run the script.

## Asking questions

```
./src/app.py
```

Then access `http://localhost:5555`.

## Configuration

You can change some defaults by creating a `rag-youtube.conf` file in the base folder.

The following options are available (values below are the default ones)

```
[General]
ollama_url=http://localhost:11434
ollama_modal=mistral:latest
persist_dir=db

[Embeddings]
model=all-MiniLM-L6-v2

[Splitter]
split_chunk_size=1000
split_chunk_overlap=200

[Search]
similarity_document_count=4
```

For the embeddings model, default is to use a [HuggingFace Sentence Transformers models](https://www.sbert.net/docs/pretrained_models.html). You can specify `ollama` to use Ollama embeddings or `openai:xxxx` to use a [OpenAI Embeddings](https://platform.openai.com/docs/guides/embeddings/what-are-embeddings).