# rag-youtube

A set of scripts to build a RAG from the videos of a YouTube channel.

This has evolved in being a playground to explore RAG applications. Notably:
- Retrieval and generation parameters can be changed for each question
- Processing information is added to response payload and can be visualized
- A number of files are dumped during processing with even more information (json format)

## Screenshots

<span>
<img src="doc/configuration.png" height="300" style="margin-right: 16px"/><img src="doc/chain.png" height="300"/>
</span>

## Prerequisites

YouTube Data API: You need a Google Cloud account and a project set up in the Google Developer Console. Enable the YouTube Data API for your project and get an API key.

Get the video ID of any of the videos of the channel you want to analyze. You can extract this directly from the URL. For instance in `https://www.youtube.com/watch?v=AS2m2rRn9Cw&t=211s` the video ID is `AS2m2rRn9Cw`.

You also need [Ollama](https://ollama.ai) installed with one model installed. Mistral or LLama2 are preferred:

```
ollama pull mistral:latest
ollama pull llama2:latest
```

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

You can change some defaults by creating a `rag-youtube.conf` file in the base folder. A good way to start is to copy `rag-youtube.sample.conf`: it contains all optios commented out with default values specified. Feel free to play with them!

For the embeddings model, default is to use a [HuggingFace Sentence Transformers models](https://www.sbert.net/docs/pretrained_models.html). You can specify `ollama` to use Ollama embeddings or `openai:xxxx` to use a [OpenAI Embeddings](https://platform.openai.com/docs/guides/embeddings/what-are-embeddings).

For enumerated options, acceptables values are:
- `chain_type`: `base`, `sources`, `conversation`
- `doc_chain_type`: `stuff`, `map_reduce`, `refine`, `map_rerank`
- `search_type`: `similarity`, `similarity_score_threshold`, `mmr`

## Debugging

You can enable langchain debugging through configuration. In that case, it is recommended to redirect the output to a text file and replace the following regex `[ \t]*"context": \[[\d, \t\n]*\],\n` with nothing to clear up the trace.
