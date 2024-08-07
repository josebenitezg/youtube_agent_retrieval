# YouTube Channel Content Analyzer with Source Attribution using Langchain and FastHTML
### Still in development
## Overview

YouTube Channel Content Analyzer with Source Attribution

## Prerequisites

```bash
pip install -r requirements.txt
```

## Export Environment Variables

Set the necessary environment variables for API access:

```bash
export GOOGLE_APPLICATION_CREDENTIALS=XX
export ANTROPHIC_API_KEY=XX
export OPENAI_API_KEY=XX
```

## Prepare the data

This script will list all the videos in a channel given a video ID, then download transcripts and metadata for each video. After that, it will ingest the data into a Chroma vector store.

Run the following command to prepare the data:

```bash
./ingest.sh
```

## Run the Application

To start the application, execute:

```bash
python main.py
```


## Usage

Once the application is running, you can interact with it to ask science questions based on the ingested video content.

## Changing the Model Provider (Work in Progress)

Model by default is set to Antrophic's Claude 3.5 sonnet

You can change the model provider in the application by modifying the following lines in your code in `models/chat_model.py`

```python
PROVIDER = "openai" # Change to your desired provider
MODEL = "gpt-4o" # Specify the model you want to use
hubegpt = HubeGPT(provider=PROVIDER, model=MODEL)
```

## Troubleshooting

If you encounter issues, check the following:

- Ensure all environment variables are set correctly.
- Verify that the required packages are installed.
- Check the logs for any error messages.

## Contributing

Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

