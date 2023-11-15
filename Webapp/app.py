from flask import Flask, render_template, request, flash, redirect, url_for
import spacy
from youtube_transcript_api import YouTubeTranscriptApi
import requests

app = Flask(__name__)
app.secret_key = '123'

nlp = spacy.load('en_core_web_sm')
def GPE_extract(text):
    tokens = nlp(text)
    token_list=[]
    for token in tokens.ents:
      if token.label_ == "GPE":
        if token.text.strip() not in token_list:
           token_list += [token.text.strip()]
    return token_list

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        url = request.form.get('youtube_url', '')
        if ("youtube.com/watch?v=" not in url) or ("This video isn't available anymore" in requests.get(url).text):
            flash('Invalid Youtbe url','error')
            return redirect(url_for('home'))
        youtube_id = url.split("=")[1][:11]
        transcript = YouTubeTranscriptApi.get_transcript(youtube_id)
        transcript_text = ""
        for line in transcript:
            transcript_text += " " + line['text'].replace("\n"," ")
            print(GPE_extract(transcript_text))
            return render_template('map.html')



    return render_template('home.html')

if __name__ == '__main__':
    app.run(debug=False)
