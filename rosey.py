import os
import requests
from google.cloud import translate_v2 as translate
import openai
import time
import html
from license import OPENAIKEY, ELEVENLABSKEY, GOOGLEKEY

# Set up Google API credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GOOGLEKEY

# Set up OpenAI & ElevenLabs API keys
openai.api_key = OPENAIKEY
elevenlabs_api_key = ELEVENLABSKEY

# Function to transcribe audio using OpenAI's API
def transcribe_audio(file_path):
    with open(file_path, "rb") as audio_file:
        response = openai.Audio.transcribe("whisper-1", audio_file)
    transcript = response["text"]
    return transcript

# Function to detect language of a given text using Google Translate API
def detect_language(text):
    translate_client = translate.Client()
    result = translate_client.detect_language(text)
    return result["language"]

# Function to get supported languages for translation from Google Translate API
def get_supported_languages():
    translate_client = translate.Client()
    languages = translate_client.get_languages()
    return languages

# Function to translate a text to a target language using Google Translate API
def translate_text(text, target_language):
    translate_client = translate.Client()
    result = translate_client.translate(text, target_language)
    translated_text = html.unescape(result["translatedText"])  # unescape any HTML entities
    return translated_text

# Function to clone a voice based on provided samples using ElevenLabs API
def clone_voice(name, description, accent, samples):
    url = "https://api.elevenlabs.io/v1/voices/add"
    headers = {
        "Accept": "application/json",
        "xi-api-key": elevenlabs_api_key
    }
    data = {
        'name': name,
        'labels': '{"accent": "' + accent + '"}',
        'description': description
    }
    files = [('files', (sample, open(sample, 'rb').read())) for sample in samples]

    response = requests.post(url, headers=headers, data=data, files=files)
    return response.json()['voice_id']

# Function to synthesize the provided text using the cloned voice using ElevenLabs API
def clone_and_synthesize_voice(text, voice_id):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
      "Accept": "application/json",
      "xi-api-key": elevenlabs_api_key
    }
    data = {
      "text": text,
      "model_id": "eleven_monolingual_v1",
      "voice_settings": {
        "stability": 0,
        "similarity_boost": 0
      }
    }
    response = requests.post(url, json=data, headers=headers, stream=True)

    # Check if translations directory exists, if not create it
    if not os.path.exists("translations"):
        os.makedirs("translations")

    # Create a unique filename based on current Unix timestamp
    timestamp = int(time.time())
    output_file = f"translations/translated_audio_{timestamp}.mp3"

    # Write response data to the file in chunks
    with open(output_file, 'wb') as f:
        for chunk in response.iter_content(chunk_size=1024):  # Adjust chunk size as needed
            if chunk:
                f.write(chunk)

    # Print the name of the output file
    print(f"Translated audio saved as '{output_file}'")

# Main function to orchestrate the process
def main():
    # Prompt user to enter the path of an audio file
    input_file = input("Enter the path to the audio file (mp3, wav, or mp4): ")

    # Transcribe the audio
    print("Transcribing audio...")
    transcript = transcribe_audio(input_file)
    print(f"Original transcript: {transcript}")

    # Detect the language of the transcript
    print("Detecting language...")
    source_language = detect_language(transcript)
    print(f"Detected language: {source_language}")

    # Get a list of supported languages for translation
    print("Getting supported languages for translation...")
    languages = get_supported_languages()
    language_names = [lang["name"] for lang in languages]
    for i, lang in enumerate(language_names):
        print(f"{i + 1}. {lang}")

    # Prompt user to select a target language for translation
    target_language_index = int(input("Enter the number of the language to translate to: ")) - 1
    target_language = languages[target_language_index]["language"]

    # Translate the transcript
    print("Translating transcript...")
    translated_text = translate_text(transcript, target_language)
    print(f"Translated text: {translated_text}")

    # Clone the voice from the audio file
    print("Cloning voice...")
    voice_samples = [input_file]  # Assuming the input file is a valid voice sample
    voice_id = clone_voice('Cloned Voice', 'This is a cloned voice.', 'US', voice_samples)
    print(f"Cloned voice ID: {voice_id}")

    # Synthesize the translated text with the cloned voice
    print("Synthesizing translated audio...")
    clone_and_synthesize_voice(translated_text, voice_id)

# If the script is run directly (not imported), then run the main function
if __name__ == "__main__":
    main()

