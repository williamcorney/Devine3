import re


def parse_season_data(output):
    """
    Helper function to parse season and episode data.
    Returns a dictionary with season data.
    """

    lines = output.split('\n')

    seasons = {}
    current_season = None

    for line in lines:
        line = line.lstrip(" │├└─")  # Clean up the line

        # Match for season information
        season_match = re.match(r"^\s*(?:[├└]──|\s*Season)\s*(\d+):\s*(\d+)\s*episodes?", line)
        if season_match:
            season_number = int(season_match.group(1))
            num_episodes = int(season_match.group(2))
            seasons[season_number] = {'number_of_episodes': num_episodes, 'episodes': []}
            current_season = season_number

        # Match for episode information with a title (e.g., "1. The Conspiracy to Murder")
        episode_match_with_title = re.match(r"^\s*(\d+)\.\s*(.+)", line)
        if episode_match_with_title and current_season is not None:
            print ('Season number:', current_season)
            episode_number = int(episode_match_with_title.group(1))
            episode_title = episode_match_with_title.group(2).strip()
            seasons[current_season]['episodes'].append((episode_number, episode_title))

        # Match for episode information without a title (e.g., "Episode 1")
        episode_match_no_title = re.match(r"^\s*Episode\s*(\d+)", line)
        if episode_match_no_title and current_season is not None:
            print ('Season number:', current_season)
            episode_number = int(episode_match_no_title.group(1))
            dummy_title = f"Episode "  # Use the episode number as the title
            seasons[current_season]['episodes'].append((episode_number, dummy_title))

    return seasons
