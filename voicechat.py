import streamlit as st
import whisper
import openai
from audiorecorder import audiorecorder
import magic
import os
import re

# Define a function to generate TTS voices using the Web Speech API
def generate_voice(text, voice):
    # Define the JavaScript code to generate the voice
    js_code = f"""
        const synth = window.speechSynthesis;
        const utterance = new SpeechSynthesisUtterance("{text}");
        utterance.voice = speechSynthesis.getVoices().filter((v) => v.name === "{voice}")[0];
        synth.speak(utterance);
    """
    # Use the components module to embed the JavaScript code in the web page
    st.components.v1.html(f"<script>{js_code}</script>", height=0)


def get_audio_record_format(orgfile):
    info = magic.from_file(orgfile).lower()
    print(f'\n\n Recording file info is:\n {info} \n\n')
    if 'webm' in info:
        return '.webm'
    elif 'iso media' in info:
        return '.mp4'
    elif 'wave' in info:
        return '.wav'
    else:
        return '.mp4'


class Conversation:
    def __init__(self, engine):
        self.engine = engine
    def generate_response(self, message):
        response = openai.Completion.create(
            engine=self.engine,
            prompt=message,
            max_tokens=1024,
            n=1,
            stop=None,
            temperature=0.2,
            presence_penalty=0.6,
            frequency_penalty=0.6
        )
        return response.choices[0].text


@st.cache  # Decorator to cache heavy setups
def init_load_setups():
    # setup asr engine
    asrmodel = whisper.load_model('base', download_root='asrmodel' )
    # setup chatGPT instance
    openai.api_key = os.getenv("OPENAI_API_KEY").strip('"')
    conversation = Conversation(engine="text-davinci-003")
    return asrmodel, conversation


# main voice chat app 
def app():
    # Put expensive initialize computation here
    st.title("Voice Assistant with chatGPT3.5")

    # get initial setup
    asr, chatgpt = init_load_setups()

    # recorder 
    audio = audiorecorder("Push to Talk", "Recording... (push again to stop)")

    if len(audio) > 0:
        # To play audio in frontend:
        st.audio(audio.tobytes())
        # To save audio to a file:
        audioname='recording.tmp'
        with open( audioname, "wb") as f:
            f.write(audio.tobytes())
        ## get record file formate based on file magics
        recordFormat = get_audio_record_format(audioname)
        os.rename(audioname, audioname + recordFormat )

        st.markdown("<b>Chat History</b> ", unsafe_allow_html=True)

        with st.spinner("Recognizing your voice commmand ..."):
            asr_result = asr.transcribe( audioname + recordFormat )
            text = asr_result["text"]
            st.markdown("<b>You:</b> " + text, unsafe_allow_html=True)
            print('ASR result is:' + text)

        st.write('')

        with st.spinner("Getting ChatGPT answer for your command ..."):
            response = chatgpt.generate_response(text)
            st.markdown("<b>chatGPT:</b> " + response, unsafe_allow_html=True)
            print('chatGPT response is: '   + response)
            spokenResponse = re.sub(r'\s+', ' ', response)
            spokenResponse = spokenResponse.lstrip().rstrip()
            #Speak the input text
            generate_voice(spokenResponse, "Google US English")


if __name__ == "__main__":
    app()