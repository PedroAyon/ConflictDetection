import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt
import seaborn as sns

# API endpoint
API_BASE_URL = 'http://127.0.0.1:5000'


# Fetch processed files data from the API
def fetch_processed_files():
    response = requests.get(f"{API_BASE_URL}/processed_files")
    if response.status_code == 200:
        return response.json()['processed_files']
    else:
        st.error("Failed to fetch data from the API.")
        return []


# Convert list of files to DataFrame for easy manipulation
def get_processed_files_df():
    files = fetch_processed_files()
    df = pd.DataFrame(files)
    df['date'] = pd.to_datetime(df['date'])  # Convert date to datetime format
    return df


# Render the table with filtering functionality
def render_files_table():
    df = get_processed_files_df()
    st.subheader("Processed Files with Conflict Detection")

    # Add filters
    agent_name_filter = st.selectbox("Filter by Agent Name", options=["All"] + df['agent_name'].unique().tolist())
    date_filter = st.date_input("Filter by Date", value=None)

    # Apply filters based on user input
    if agent_name_filter != "All":
        df = df[df['agent_name'] == agent_name_filter]
    if date_filter:
        df = df[df['date'].dt.date == date_filter]

    # Display the table with a play button for audio
    st.dataframe(df[['id', 'file_path', 'text_extracted', 'conflictive', 'agent_name', 'date']])

    # Manage selected file in session state
    if 'selected_audio' not in st.session_state:
        st.session_state.selected_audio = None

    # Add play button to play the audio
    selected_row = st.selectbox("Select the File ID to Play", df['id'].tolist(), key="file_selector")

    # Check if an audio is selected and store it in session state
    if selected_row != st.session_state.selected_audio:
        st.session_state.selected_audio = selected_row

    if st.session_state.selected_audio is not None:
        selected_file = df[df['id'] == st.session_state.selected_audio]['file_path'].values[0]
        audio_url = f"{API_BASE_URL}/audio/{selected_file.split('/')[-1]}"  # Get the file name from the path
        st.audio(audio_url)

    return df, agent_name_filter


# Render bar graph of conflictive vs non-conflictive conversations
def render_conflict_graph(df):
    st.subheader("Conflictive vs Non-Conflictive Conversations")

    # Filter the data for conflictive and non-conflictive conversations
    conflict_counts = df['conflictive'].value_counts()

    # Plot the bar chart
    fig, ax = plt.subplots()
    sns.barplot(x=conflict_counts.index, y=conflict_counts.values, ax=ax)
    ax.set_xlabel("Conflict Status")
    ax.set_ylabel("Count")
    ax.set_title("Conflictive vs Non-Conflictive Conversations")
    st.pyplot(fig)


# Render time series graph for conflicts over time
def render_time_series_graph(df):
    st.subheader("Conflicts Over Time")

    # Group by date and conflictive status
    df['date'] = df['date'].dt.date
    conflicts_over_time = df.groupby(['date', 'conflictive']).size().unstack().fillna(0)

    # Plot the time series graph
    fig, ax = plt.subplots(figsize=(10, 6))
    conflicts_over_time.plot(kind='bar', stacked=True, ax=ax)
    ax.set_xlabel("Date")
    ax.set_ylabel("Number of Conversations")
    ax.set_title("Conflicts Over Time")
    st.pyplot(fig)

from wordcloud import WordCloud

def render_word_cloud(df):
    st.subheader("Word Cloud of Conflictive Conversations")

    # Get the text from conflictive conversations
    conflictive_text = ' '.join(df[df['conflictive'] == True]['text_extracted'])

    # Generate the word cloud
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(conflictive_text)

    # Display the word cloud
    st.image(wordcloud.to_array(), use_container_width=True)



# Main function to display the app
def main():
    st.title("Customer Support Analysis Dashboard")

    # Show the processed files table and allow playback, also get the filtered data and agent name filter
    df, agent_name_filter = render_files_table()

    # Apply agent filter to the graphs
    if agent_name_filter != "All":
        df = df[df['agent_name'] == agent_name_filter]

    # Show the bar graph of conflictive vs non-conflictive conversations
    render_conflict_graph(df)

    # Show the time series graph of conflicts over time
    render_time_series_graph(df)

    render_word_cloud(df)

if __name__ == "__main__":
    main()
