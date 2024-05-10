from flask import Flask, jsonify
from plexapi.server import PlexServer
import requests
from dotenv import load_dotenv
import os
import musicbrainzngs
import sys

load_dotenv()

app = Flask(__name__)


def power_on_amp():
    print(os.getenv('HASS_DOMAIN'), file=sys.stderr)
    url = f"{os.getenv('HASS_DOMAIN')}/api/services/script/turn_on"
    data = {
        "entity_id": f"script.{os.getenv('HASS_SCENE')}"
    }
    print(data)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('HASS_TOKEN')}"
    }

    r = requests.post(url, headers=headers, json=data, verify=False)
    print(r.text, file=sys.stderr)


def try_musicbrainz(barcode):
    musicbrainzngs.set_useragent(
        os.getenv("MUSICBRAINZ_APP_NAME"), "0.1", os.getenv("MUSICBRAINZ_EMAIL")
    )
    try:
        result = musicbrainzngs.search_releases(barcode=barcode, strict=True)
        if result["release-list"]:
            release = result["release-list"][0]
            album_name = release["title"]
            artist = release.get("artist-credit", [{}])[0].get("name", "Unknown Artist")
            genre = "Unknown"
            year = release.get("date", "Unknown")[:4]
            return {
                "album_name": album_name,
                "artist": artist,
                "genre": genre,
                "year": year,
            }
        else:
            return "No matching releases found."
    except musicbrainzngs.MusicBrainzError as e:
        return f"Error querying MusicBrainz: {e}"


def get_album_metadata(barcode):
    consumer_key = os.getenv("DISCOGS_CONSUMER_KEY")
    consumer_secret = os.getenv("DISCOGS_CONSUMER_SECRET")
    base_url = "https://api.discogs.com/database/search"
    headers = {"User-Agent": f"{os.getenv('DISCOGS_APP_NAME')}/1.0"}
    params = {"barcode": barcode, "key": consumer_key, "secret": consumer_secret}

    try:
        response = requests.get(base_url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        if data["results"]:
            album_info = data["results"][0]
            return {
                "artist": album_info.get("title", "").split(" - ")[0],
                "album_name": album_info.get("title", "").split(" - ")[1],
                "year": album_info.get("year", "Unknown"),
                "genre": album_info.get("genre", ["Unknown"])[0],
            }
        else:
            musicbrainz_results = try_musicbrainz(barcode)
            return musicbrainz_results
    except requests.RequestException as e:
        return f"An error occurred: {e}"


def search_lms(artist, album_name):
    album_title = f"{artist} - {album_name}"

    print('Searching for', album_title, flush=True)

    search_body = {
        "id": 0,
        "method": "slim.request",
        "params": [
            0,
            [
                "albums",
                0,
                20,
                f"search:{album_name}",
                "tags:la"
            ]
        ]
    }

    print(search_body, flush=True)

    lms_url = os.getenv("LMS_URL")
    lms_headers = {"Content-Type": "application/json"}

    lms_query = requests.post(lms_url, headers=lms_headers, json=search_body)

    print(lms_query.text, flush=True)

    if lms_query:
        lms_query = lms_query.json()
        album_loop = lms_query.get('result', {}).get('albums_loop')
        if album_loop:
            print(album_loop, flush=True)
            if len(album_loop) == 1:
                top_result = album_loop[0][('id')]
            elif len(album_loop) > 1:
                top_result = [x['id'] for x in album_loop if artist in x['artist']]
                if top_result:
                    top_result = top_result[0]
                else:
                    located_artists = [x['artist'] for x in album_loop]
                    unique_artists = set(located_artists)
                    if len(unique_artists) == 1:
                        top_result = [x['id'] for x in album_loop]
                        top_result = top_result[0]
                    else:
                        return "Multiple results found but none matched the artist"
            else:
                return None

            play_body = {
                "id": 0,
                "method": "slim.request",
                "params": [
                    os.getenv('LMS_PLAYER'),
                    [
                        "playlistcontrol",
                        "cmd:load",
                        f"album_id:{top_result}"
                    ]
                ]
            }
            print(play_body, flush=True)
            lms_play_result = requests.post(lms_url, headers=lms_headers, json=play_body)
            print(lms_play_result.text, flush=True)


def search_plex(artist, album_name):
    baseurl = os.getenv("PLEX_DOMAIN")
    token = os.getenv("PLEX_TOKEN")
    plex_client = os.getenv("PLEX_CLIENT")
    plex_section = os.getenv("PLEX_SECTION")

    plex = PlexServer(baseurl, token)
    client = plex.client(plex_client)

    album_title = f"{artist} - {album_name}"

    q = plex.search(album_name, mediatype="album")
    if q:
        client.playMedia(q[0])
    else:
        music = plex.library.section(plex_section)
        for artist in music.search(libtype="artist", title=artist):
            if artist:
                for a in artist:
                    if a.title.lower() in album_title.lower():
                        client.playMedia(a)

                        return
        album_title = f"{artist} - {album_name}"
        q = plex.search(album_title)
        if q:
            client.playMedia(q[0])


@app.route("/<barcode>", methods=["GET"])
def handle_request(barcode):
    # power_on_amp()
    metadata = get_album_metadata(barcode)
    if isinstance(metadata, dict):
        # search_plex(metadata["artist"], metadata["album_name"])
        search_lms(metadata["artist"], metadata["album_name"])
        return jsonify(metadata)
    else:
        return jsonify({"error": metadata}), 404


@app.route("/<barcode>/test", methods=["GET"])
def test_barcode(barcode):
    power_on_amp()
    metadata = get_album_metadata(barcode)
    return jsonify(metadata)


if __name__ == "__main__":
    app.run(debug=True)
