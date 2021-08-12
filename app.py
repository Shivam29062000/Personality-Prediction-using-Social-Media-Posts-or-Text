# Flask Packages ---------------------------------------------------------------------------------------------------
from tweepy import Cursor, error
# Class imported our created python file
from twitterscrap import TwitterClient, TweetAnalyzer
from flask import Flask
from flask import render_template, request
from bs4 import BeautifulSoup
import pickle
import re
import os

# Dash Packages ---------------------------------------------------------------------------------------------------
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import plotly.graph_objs as go
import pandas as pd

# For Personality Prediction ---------------------------------------------------------------------------------------
text_pred_model = pickle.load(open(r'./ml-part/NB-model.pkl', 'rb'))


def cleanText(text):
    text = BeautifulSoup(text, "lxml").text
    text = re.sub(r'\|\|\|', r' ', text)
    text = re.sub(r'http\S+', r'<URL>', text)
    return text


jobs = {
    "ISTJ": ["Dentist", "Certified public accountant", "Supply chain manager", "Business analyst"],
    "INFJ": ["Counselor", "Writer", "Scientist", "Librarian", "Psychologist"],
    "INTJ": ["Musical performer", "Managing editor", "Photographer", "Financial advisor", "Marketing manager", "Teacher", "Physical therapist"],
    "ENFJ": ["Guidance counselor", "Sales manager", "HR director", "Art director", "Public relations manager"],
    "ISTP": ["Technician", "Construction worker", "Engineer", "Forensic scientist", "Inspector"],
    "ESFJ": ["Office manager", "Technical support specialist", "Museum curator", "Psychologist", "Medical researcher"],
    "INFP": ["Copywriter", "HR manager", "Physical therapist", "Mental health professional", "Artist", "Photographer"],
    "ESFP": ["Event planner", "Professional entertainer", "Sales representative", "Cosmetologist", "Flight attendant", "Tour guide"],
    "ENFP": ["Reporter or news anchor", "Editor", "Musician", "Product manager", "Elementary school teacher", "Personal trainer", "Social worker"],
    "ESTP": ["Firefighter", "Paramedic", "Creative director", "Project coordinator", "Construction manager"],
    "ESTJ": ["Judge", "Coach", "Financial officer", "Hotel manager", "Real estate agent"],
    "ENTJ": ["Business administrator", "Public relations specialist", "Mechanical engineer", "Judge", "Construction manager", "Astronomer"],
    "INTP": ["Composer", "Professor", "Writer", "Producer", "Biomedical engineer", "Marketing consultant", "Web developer"],
    "ISFJ": ["Accountant", "Financial clerk", "Bank teller", "Research analyst", "Accountant", "Administrative manager", "Photographer", "Elementary teacher"],
    "ENTP": ["Attorney", "Copywriter", "Financial planner", "Psychologist", "Systems analyst", "Creative director", "Operations specialist"],
    "ISFP": ["Bookkeeper", "Social media manager", "Optician", "Veterinarian", "Archeologist", "Social worker", "Occupational therapist"],
}

# For Twitter Prediction -------------------------------------------------------------------------------------------

twitter_client = TwitterClient()
tweet_analyzer = TweetAnalyzer()

api = twitter_client.get_twitter_client_api()

# Flask app - initialize -------------------------------------------------------------------------------------------
server = Flask(__name__)

server.secret_key = os.urandom(28)

# Flask App ---------------------------------------------------------------------------------------------------------
# Home page


@server.route("/")
def home():
    return render_template("index.html")


# Personality prediction using text
@server.route("/text-pred", methods=["POST", "GET"])
def textPred():
    if request.method == "POST":
        user = request.form["txt"]
        user = cleanText(user)
        user = [user]
        user_pred = text_pred_model.predict(user)
        print(user_pred)
        return render_template("text-result.html", result={user_pred[0]})
    else:
        return render_template("text-pred.html")


# Dash app for Twitter Personality Prediction --------------------------------------------------------------------------------------------
app = dash.Dash(__name__, server=server,
                url_base_pathname="/twitter-pred/", title="Twitter Personality")
app.layout = html.Div(
    children=[
        html.H1(children="Twitter Personality Prediction"),
        dcc.Input(id="user", value='', type="text",
                  placeholder="Twitter Handle", debounce=True, autoComplete='on', className="input-box"),
        html.Button(id="submit-btn", n_clicks=0,
                    children="Predict", className="predict-btn"),
        html.Div(id="twitter-graphs"),
    ]
)


@app.callback(
    Output(component_id="twitter-graphs", component_property="children"),
    [Input(component_id="submit-btn", component_property="n_clicks")],
    [State(component_id="user", component_property="value")],
    prevent_initial_call=True
)
def update_graphs(n_clicks, user_handle):
    print("Clicks: ", n_clicks)
    if user_handle is None:
        raise PreventUpdate
    else:
        try:
            user = api.get_user(user_handle)
            print("-----------------------------------")
            print("Name:", user.name)
            print("Name:", user.screen_name)
            print("Number of tweets: " + str(user.statuses_count))
            print("followers_count: " + str(user.followers_count))
            print("Account location: ", user.location)
            print("Account created at: ", user.created_at)
            print("Account geo enabled: ", user.geo_enabled)
            print()

            # Getting name of the user
            screen_name = str(user_handle)

            # Getting tweets of the user with details
            tweets = api.user_timeline(screen_name, count=20)

            # Cleaning the user tweets collected
            data_user = []
            df = tweet_analyzer.tweets_to_data_frame(tweets)
            for tweet in df['Tweets']:
                data_user.append((tweet_analyzer.clean_tweet(tweet)))

            # Getting user's friends' tweets with details
            friends = []
            friends_name = []
            for friend in Cursor(api.friends, screen_name).items(5):
                print("Name:", friend.name)
                print("Name:", friend.screen_name)
                print("Number of tweets: " + str(friend.statuses_count))
                print("followers_count: " + str(friend.followers_count))
                print("Account location: ", friend.location)
                print("Account created at: ", friend.created_at)
                print("Account geo enabled: ", friend.geo_enabled)
                print()
                friends.append((friend.screen_name))
                friends_name.append((friend.name))

            print("-----------------------------------")
            print()

            # Cleaning the data of each of the friend of the user
            data_friends = []
            for friend in friends:
                cleaned = []
                tt = api.user_timeline(friend, count=20)
                df = tweet_analyzer.tweets_to_data_frame(tt)
                for tweet in df['Tweets']:
                    cleaned.append((tweet_analyzer.clean_tweet(tweet)))
                data_friends.append(cleaned)

            c = text_pred_model.predict(data_user)
            print(c)

            # Prediction for user's twitter handle
            output = pd.DataFrame({"col1": c})
            max_output_personality = output["col1"].value_counts().keys()[0]
            max_output_count = output["col1"].value_counts()[0]

            print(max_output_personality, ": ", max_output_count)

            job_disp = []
            for x in jobs[max_output_personality]:
                job_disp.append(html.Li(children=x))

            # Prediction for friends
            output_friends = []
            of_plots = []
            for i in range(len(friends)):
                output_friends.append(pd.DataFrame(
                    {"col1": text_pred_model.predict(data_friends[i])}))
                of_plots.append(dcc.Graph(id="friend-graph-"+str(i+1), className="graph-tile", figure={"data": [
                                go.Pie(labels=output_friends[i]["col1"].unique(), values=output_friends[i]["col1"].value_counts())], "layout": {"title": friends_name[i] + " (" + friends[i] + ")"}}))

            return [
                html.H2(children="User Personality", className="head"),
                html.Div(children=[dcc.Graph(id="user-graph", className="graph-tile", figure={"data": [go.Pie(labels=output["col1"].unique(
                ), values=output["col1"].value_counts())], "layout": {"title": str(user.name) + " (" + screen_name + ")"}})], className="g"),
                html.H3(children="Career Prediction for " + str(user.name) + " based on tweets", className="sub-head"),
                html.P(children="Based on " + "{}%".format(max_output_count*5)+ " of the user's tweets, the predicted personality is " + max_output_personality + ". The user will be suitable for the following job roles:", className="sub-p"),
                html.Ul(children=job_disp, className="jlist"),
                html.H2(children="Follower Personalities", className="head"),
                html.Div(children=of_plots, className="board"),
            ]

        except error.TweepError as e:
            return html.H3(children=str(e))


if __name__ == "__main__":
    server.run()
