import os
from plexapi.server import PlexServer
import json
import shutil

def get_realpath(file):
    return os.path.join(os.path.realpath(os.path.dirname(__file__)), file)

with open(get_realpath('config.json')) as f:
    config = json.load(f)

def GetAllShows():
    plex = PlexServer(config["PLEX_URL"], config["PLEX_TOKEN"])
    shows = []
    for section in plex.library.sections():
        if section.type == "show":
            for show in section.all():
                shows.append(show.title)
    return shows


def GetAllMovies():
    plex = PlexServer(config["PLEX_URL"], config["PLEX_TOKEN"])
    movies = []
    for section in plex.library.sections():
        if section.type == "movie":
            for movie in section.all():
                movies.append(movie.title)
    return movies

def DeleteShow(show_title):
    plex = PlexServer(config["PLEX_URL"], config["PLEX_TOKEN"])
    for section in plex.library.sections():
        if section.type == "show":
            for show in section.all():
                if show.title.strip().lower() == show_title.strip().lower():
                    show.delete()
                    try:
                        folders = set()
                        for season in show.seasons():
                            for episode in season.episodes():
                                try:
                                    file_path = episode.media[0].parts[0].file
                                    folder_name = file_path.replace(config["SHOW_PATH"], "")[1:].split("/")[0]
                                    folders.add(folder_name)
                                except Exception as e:
                                    continue  # skip episodes with missing files
                        for folder_name in folders:
                            folder_path = os.path.join(config["SHOW_PATH"], folder_name)
                            if config["SHOW_PATH"] in folder_path and len(folder_path.split(f'{config["SHOW_PATH"]}/')[1]) > 1:
                                shutil.rmtree(folder_path)
                    except Exception as e:
                        raise Exception(f"Error removing show folders: {e}")
        

def DeleteMovie(movie_title):
    plex = PlexServer(config["PLEX_URL"], config["PLEX_TOKEN"])
    for section in plex.library.sections():
        if section.type == "movie":
            for movie in section.all():
                if movie.title.strip().lower() == movie_title.strip().lower():
                    movie.delete()
                    try:
                        folder_name = movie.media[0].parts[0].file.replace(config["MOVIE_PATH"], "")[1:].split("/")[0]
                        folder_path = os.path.join(config["MOVIE_PATH"], folder_name)
                        if config["MOVIE_PATH"] in folder_path and len(folder_path.split(f'{config["MOVIE_PATH"]}/')[1]) > 1:
                            shutil.rmtree(folder_path)
                    except Exception as e:
                        raise Exception(f"Error removing movie folders: {e}")

def RefreshLibrary():
    plex = PlexServer(config["PLEX_URL"], config["PLEX_TOKEN"])
    for section in plex.library.sections():
        section.refresh()