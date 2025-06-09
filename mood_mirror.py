import streamlit as st
import pandas as pd
from textblob import TextBlob
from datetime import datetime
import os
from transformers import pipeline
import emoji  
import re 
import calplot 
import matplotlib.pyplot as plt
import speech_recognition as sr


# Setting up the Streamlit page configuration
st.set_page_config(page_title="Mood Mirror", layout="centered")

# Inject custom CSS
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

local_css("style.css")



# Load huggingface sentiment model 
sentiment_model = pipeline("sentiment-analysis")
 

# Function to classify mood from text
def classify_mood(text):
    emoji_mood_map = {
        '😊': 'Happy', '😄': 'Happy', '😁': 'Happy', '😎': 'Happy', '❤️': 'Happy', '🥰': 'Happy', '😇': 'Happy',
        '😢': 'Sad', '😭': 'Sad', '😞': 'Sad', '😔': 'Sad', '💔': 'Sad', '😩': 'Sad', '😖': 'Sad',
        '😐': 'Neutral', '😶': 'Neutral', '😑': 'Neutral', '🤔': 'Neutral', '😬': 'Neutral'
    }

    # Check for emojis in the input text
    for emoji, mood in emoji_mood_map.items():
        if emoji in text:
            return mood

    # Fallback to TextBlob for regular text
    polarity = TextBlob(text).sentiment.polarity
    if polarity > 0.3:
        return "Happy"
    elif polarity < -0.3:
        return "Sad"
    else:
        return "Neutral"

# Load or create mood data file 
def load_data():
    if os.path.exists("mood_data.csv"):
        return pd.read_csv("mood_data.csv")
    else:
        return pd.DataFrame(columns = ["user","mood_text","mood","date"])

# Save new mood entry
def save_mood(user,mood_text,mood):
    df =  load_data()
    new_row  = {
        "user":user,
        "mood_text":mood_text,
        "mood":mood,
        "date":datetime.now().strftime("%Y-%m-%d")

    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv("mood_data.csv",index= False)

# Mood sync insight 

def mood_sync_insight(df):
    if df.empty:
        return "No mood data available for analysis."

    # Step 1: Convert date column to datetime (in case it's not)
    df['date'] = pd.to_datetime(df['date']).dt.date

    # Step 2: Get most common mood for each user per day
    mode_df = (
        df.groupby(['date', 'user'])['mood']
        .agg(lambda x: x.mode().iloc[0] if not x.mode().empty else x.iloc[0])
        .unstack()
        .dropna()
    )

    if mode_df.empty:
        return "Not enough data where both users recorded mood on the same day."

    # Step 3: Compare moods for sync
    match_count = (mode_df['Girlfriend'] == mode_df['Boyfriend']).sum()
    total_days = mode_df.shape[0]
    match_percentage = (match_count / total_days) * 100

    if match_percentage > 70:
        return f"💖 Great! You both are emotionally in sync {match_percentage:.1f}% of the time!"
    elif match_percentage > 40:
        return f"😊 You two match moods {match_percentage:.1f}% of the time. Keep connecting!"
    else:
        return f"😕 Only {match_percentage:.1f}% mood sync. Try to understand each other better."

    


    


# Stream Lit app starts here 
st.markdown("<h1 style='text-align: center; color: #ff4b4b;'>❤️ Mood Mirror: Relationship Mood Tracker ❤️</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center;'>A beautiful way to log, reflect and connect over your daily emotions 💞</h4>", unsafe_allow_html=True)
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    user = st.selectbox("Who are you?", ["Girlfriend", "Boyfriend"])
   
with col2:
    mood_text = st.text_input("How are you feeling today? (📝 Text, emoji, or sentence)")   

st.markdown("---")
st.subheader("🎙️ Optional: Record your mood")

if st.button("Record Voice"):
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("Listening... Please speak.")
        try:
            audio = recognizer.listen(source, timeout=5)
            text = recognizer.recognize_google(audio)
            st.success(f"You said: {text}")
            mood_text = text  # Update the mood_text with transcribed text
        except sr.WaitTimeoutError:
            st.error("Listening timed out. Try again.")
        except sr.UnknownValueError:
            st.error("Could not understand audio.")
        except sr.RequestError as e:
            st.error(f"Could not request results; {e}")
if st.button ("Submit mood"):
    if mood_text.strip() == "":
        st.warning("Please enter your mood description !")
    else:
        mood = classify_mood(mood_text)
        save_mood(user,mood_text,mood)
        st.success(f" Mood saved as **{mood}** for **{user}**!")


# Load data for visualization
df = load_data()

if not df.empty :
    st.subheader("Mood Data Overview")

    # Count moods per user 
    mood_counts = df.groupby(["user","mood"]).size().unstack(fill_value = 0)
    st.write("Mood counts per user:")
    st.dataframe(mood_counts)

    # Line chart of moods over time for each user 
    st.subheader("Mood Timeline")
    df['date'] = pd.to_datetime(df['date'])
    df_sorted = df.sort_values("date")

    # map moods to numbers for plotting
    mood_map = {"Sad":0, "Neutral":1 , "Happy":2}
    df_sorted['mood_num'] = df_sorted['mood'].map(mood_map)

    # Create seperate lines for each user 
    gf_df = df_sorted[df_sorted['user']== "Girlfriend"]
    bf_df = df_sorted[df_sorted['user']== "Boyfriend"]

    import plotly.graph_objects as go
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=gf_df['date'],
        y=gf_df['mood_num'],
        mode='lines+markers',name='Girlfriend',
        line=dict(color="pink")
    ))

    fig.add_trace(go.Scatter(
        x=bf_df['date'],
        y=bf_df['mood_num'],
        mode='lines+markers',name='Boyfriend',
        line=dict(color="blue")


    ))

    fig.update_layout(
        yaxis = dict(
            tickmode = "array",
            tickvals = [0,1,2],
            ticktext = ["Sad", "Neutral", "Happy"]

        ),
        xaxis_title = "Date",
        yaxis_title = "Mood",
        title = "Mood Timeline over Time "
    )
    st.plotly_chart(fig)

else:
    st.info("No mood data found. Submit some mmoods!")

st.markdown("### 💞 Mood Sync Insight")
insight = mood_sync_insight(df)
st.info(insight)


# Calender heatmap
st.subheader("📅 Calendar Mood Heatmap")

# Convert moods to scores for heatmap
mood_score_map = {"Sad": -1, "Neutral": 0, "Happy": 1}
df["mood_score"] = df["mood"].map(mood_score_map)
df["date"] = pd.to_datetime(df["date"])

# Select user for whom to show the heatmap
selected_user = st.selectbox("Select user to view mood calendar:", df["user"].unique())

# Filter by user
user_df = df[df["user"] == selected_user]

if not user_df.empty:
    # Group by date and average mood score per day
    daily_moods = user_df.groupby("date")["mood_score"].mean()

    # Plot calendar heatmap
    fig, ax = calplot.calplot(
        daily_moods,
        cmap="RdYlGn",  # red = sad, yellow = neutral, green = happy
        colorbar=True,
        how="mean",
        suptitle=f"{selected_user}'s Mood Calendar"
    )
    st.pyplot(fig)
else:
    st.write("No data available for selected user.")










