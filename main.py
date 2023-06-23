from bs4 import BeautifulSoup
from flask import Flask, render_template,request
from pyaiml21 import Kernel
from glob import glob
from nltk.corpus import wordnet
from py2neo import Graph
import nltk
from nltk import word_tokenize, pos_tag
from nltk.corpus import wordnet
from nltk.tokenize import word_tokenize, sent_tokenize
import requests
app = Flask(__name__)
Bot = Kernel()
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('wordnet')
graph=Graph("bolt://localhost:7687", auth=("neo4j", "123456789"))

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')



@app.route('/register1', methods=['POST'])
def register1():
    username=request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    graph.run(f"CREATE(n:person{{name:\"{username}\",email:\"{email}\",password:\"{password}\"}})")
    return render_template('login.html')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/login_validation', methods=['POST'])
def login_validation():
    email = request.form.get('email')
    password = request.form.get('password')
    print(email,password)
    email_value1=graph.run(f"MATCH(n:person{{email:\"{email}\",password:\"{password}\"}}) return n")
    # Retrieve user from Neo4j
    email_value=list(email_value1)
    print(email_value)
    if email_value:
        # Successful login, redirect to the home page
        return render_template('home.html')
    else:
        # Invalid login, show error message or redirect back to login page
        return render_template('login.html', error_message='Invalid credentials')

aiml_files = glob("files/*")
for file in aiml_files:
    Bot.learn_aiml(file)
def get_nouns(query):
    sentences = sent_tokenize(query)
    nouns = []
    for sentence in sentences:
        tokenized = word_tokenize(sentence)
        tagged = pos_tag(tokenized)
        nouns.extend([word for word, pos in tagged if pos.startswith('NNP')])
    return nouns
def get_wek(query):
    tokenized = word_tokenize(query)
    tagged = pos_tag(tokenized)
    if tagged[0]=='NNP':
        return tagged[0]


def get_wikipedia_paragraph(noun):
    # Format the noun to be included in the Wikipedia URL
    formatted_noun = noun.replace(" ", "_")

    # Create the Wikipedia URL
    url = f"https://en.wikipedia.org/wiki/{formatted_noun}"

    # Send a GET request to the Wikipedia page
    response = requests.get(url)

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(response.content, "html.parser")

    # Find the first paragraph (excluding any subheadings) on the Wikipedia page
    paragraphs = soup.find_all("p", class_=None)  # Exclude paragraphs with class attribute
    first_paragraph = paragraphs[0].get_text()

    # Return the extracted paragraph
    return first_paragraph


def search_wordnet(noun):
    synsets = wordnet.synsets(noun)
    if synsets:
        first_synset = synsets[0]
        definition = first_synset.definition()
        examples = first_synset.examples()
        response = f"Word: {noun}\nDefinition: {definition}\nExamples: {examples}"
        return response

    else:
        return f"No synsets found for {noun} in WordNet."



def is_first_letter_noun(sentence):
    # Tokenize the sentence into words
    words = nltk.word_tokenize(sentence)

    # Perform part-of-speech tagging
    pos_tags = nltk.pos_tag(words)

    if pos_tags:
        # Get the POS tag of the first word
        first_word_pos = pos_tags[0][1]

        # Check if the POS tag starts with 'N' (noun)
        if first_word_pos.startswith('N'):
            return words[0]

    return False

@app.route("/get")
def get_bot_response():
    query = request.args.get('msg')
    nouns = get_nouns(query)
    nn=is_first_letter_noun(query)
    print(nn)
    if nouns:
        for noun in nouns:
            response = search_wordnet(noun)
            return (str(response))
    elif nn:
        response=get_wikipedia_paragraph(nn)
        return (str(response))
    else:
        response = Bot.respond(query, 'user')
        return (str(response))

if __name__=="__main__":
    app.run(host='0.0.0.0',port='5000')
