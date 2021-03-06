from pytag import Audio
import subprocess
import re
import os


class Util:
    TIME_DIFFERENCE_LOWER_BOUND = -15 # At most how many seconds less a video can be to be valid
    TIME_DIFFERENCE_UPPER_BOUND = 60 # At most how many seconds longer a video can be to be valid
    NORMALIZED_RMS_DECIBELS = -18 # ffmpeg-normalize defaults to -26
    NORMALIZED_SONG_PREFIX = "normalized" # a dash is automatically added after the prefix

    @staticmethod
    def html_to_ascii(s):
        """
        Converts html encoding to ascii in a String and returns a new String

        :param s: A String
        :return: A new String replacing all html encoding with ascii representation
        """
        html_codes = [
            ["'", '&#39;'],
            ['"', '&quot;'],
            ['>', '&gt;'],
            ['<', '&lt;'],
            ['&', '&amp;']
        ]
        for code in html_codes:
            s = s.replace(code[1], code[0])

        return s

    @staticmethod
    def remove_invalid_filename_chars(s):
        """
        Takes a String and removes any characters that are invalid filename characters

        :param s: A String
        :return: A String with any invalid filename characters removed
        """
        invalid_chars = [["/", "_"]]
        for char in invalid_chars:
            s = s.replace(char[0], char[1])

        return s

    @staticmethod
    def get_song_filename(song):
        """
        Returns a String representing the file name of a song

        :param song: a dictionary of song info. Must contain fields for 'title', 'artist', 'album' and 'time'
        :return: A String representing the filename of the song
        """
        return Util.remove_invalid_filename_chars(Util.html_to_ascii(song["artist"] + " - " + song["title"] + ".mp3"))

    @staticmethod
    def get_song_filename_and_folder(song, folder):
        """
        Returns a String representation of a song and the folder it belongs to

        :param song: a dictionary of song info. Must contain fields for 'title', 'artist', 'album' and 'time'
        :param folder: the folder the song belongs to
        :return: A string representing the song and it's folder
        """
        return Util.get_song_filename(song) + "\t\t" + folder

    @staticmethod
    def get_best_song_from_search(song, song_search_info):
        """
        Takes a list of dictionaries, containing song search 'title', 'url', and 'time' (in seconds), and return the
        search result information for the best song

        :param song: A dictionary containing the song info. Must include 'title', 'artist', album', and 'time' fields.
        :param song_search_info: A list of dictionaries containing the info for a search for that song.
                                 Must contain 'title', 'url', and 'time' (in seconds) fields.
        :return:
        """
        for search_result in song_search_info:
            song_title_and_artist = song["title"] + " " + song["artist"]
            song_time = song["time"]
            vid_title = search_result["title"]
            vid_url = search_result["url"]

            # Can't find soundcloud song times, so if one isn't provided assume it's the same
            if search_result["time"] is None:
                vid_time = song_time
            else:
                vid_time = search_result["time"]

            # If the video a cover (not by the artist)
            if re.search(r"(?<![a-z])cover(?![a-z])", vid_title, re.IGNORECASE) is not None \
                    and re.search(r"(?<![a-z])cover(?![a-z])", song_title_and_artist, re.IGNORECASE) is None:
                continue
            # if the video is a live performance
            elif re.search(r"(?<![a-z])live(?![a-z])", vid_title, re.IGNORECASE) is not None \
                    and re.search(r"(?<![a-z])live(?![a-z])", song_title_and_artist, re.IGNORECASE) is None:
                continue
            # If the video is a music video
            elif (re.search(r"music([^a-z])video", vid_title, re.IGNORECASE) is not None
                  and re.search(r"music([^a-z])video", song_title_and_artist, re.IGNORECASE) is None) \
                    or (re.search(r"(?<![a-z])official(?![a-z])", vid_title, re.IGNORECASE) is not None
                        and re.search(r"(?<![a-z])official(?![a-z])", song_title_and_artist, re.IGNORECASE) is None
                        and re.search(r"(?<![a-z])lyric(s)?(?![a-z])", vid_title, re.IGNORECASE) is None
                        and re.search(r"(?<![a-z])audio(?![a-z])", vid_title, re.IGNORECASE) is None
                        and re.search(r"(?<![a-z])audio(?![a-z])", song_title_and_artist, re.IGNORECASE) is None):
                continue
            # If the video is an instrumental
            elif re.search(r"(?<![a-z])instrumental(?![a-z])", vid_title, re.IGNORECASE) is not None \
                    and re.search("(?<![a-z])instrumental(?![a-z])", song_title_and_artist, re.IGNORECASE) is None:
                continue
            # If the video is an acoustic version
            elif re.search(r"(?<![a-z])acoustic(?![a-z])", vid_title, re.IGNORECASE) is not None \
                    and re.search("(?<![a-z])acoustic(?![a-z])", song_title_and_artist, re.IGNORECASE) is None:
                continue
            # If the video is a reaction video
            elif re.search(r"(?<![a-z])react(ion)?(?![a-z])", vid_title, re.IGNORECASE) is not None \
                    and re.search(r"(?<![a-z])react(ion)?(?![a-z])", song_title_and_artist, re.IGNORECASE) is None:
                continue
            # If the video is a behind the scenes video
            elif re.search(r"(?<![a-z])Behind(?![a-z]).(?<![a-z])The(?![a-z]).(?<![a-z])Scenes(?![a-z])", vid_title,
                           re.IGNORECASE) is not None\
                    or (re.search(r"(?<![a-z])bts(?![a-z])", vid_title, re.IGNORECASE) is not None
                      and re.search(r"(?<![a-z])bts(?![a-z])", song_title_and_artist, re.IGNORECASE) is None):
                continue
            # If the video is a mix or remix
            elif re.search(r"(?<![a-z])(re)?mix(?![a-z])", vid_title, re.IGNORECASE) is not None \
                    and re.search(r"(?<![a-z])(re)?mix(?![a-z])", song_title_and_artist, re.IGNORECASE) is None:
                continue
            # If the video is a performance
            elif re.search(r"(?<![a-z])perform(s)?(ance)?(?![a-z])", vid_title, re.IGNORECASE) is not None \
                    and re.search(r"(?<![a-z])perform(s)?(ance)?(?![a-z])", song_title_and_artist, re.IGNORECASE) is None:
                continue
            # If the video does not have the title/artist of the song
            elif re.search(r".*" + re.escape(song["title"]) + r".*", vid_title, re.IGNORECASE) is None\
                    or re.search(r".*" + re.escape(song["artist"]) + r".*", vid_title, re.IGNORECASE) is None:
                continue
            # If the video's time does not fall withing a range of the song's time
            elif vid_time - song_time > Util.TIME_DIFFERENCE_UPPER_BOUND or vid_time - song_time < Util.TIME_DIFFERENCE_LOWER_BOUND:
                continue
            else:
                return search_result

        return None

    @staticmethod
    def rename_song_file(filepath, song_filename, song):
        """
        Takes a filepath pointing to where the file exists, the song to be renamed
        and renames the file to the name returned by get_song_filename

        :param filepath: The filepath to the song file
        :param song: The song of the file to be renamed
        :return: void
        """
        new_name = Util.get_song_filename(song)
        os.rename(filepath + song_filename, filepath + new_name)

    @staticmethod
    def get_song_in_filepath(filepath, title, url=None):
        """
        Given the filepath to the folder containing the song, the song, and the url of the song and returns
        the filename of the song

        :param filepath: The path where the song exists
        :param title: the title of the song search result
        :param url: The url of the song
        :return: the filename of the song if found, None otherwise
        """
        # downloads from youtube are named with the title of the vid followed by a dash and the 11 character unique
        # ID of the video that's also found at the end of the url
        # Eg. Green Day - Bang Bang (Official Lyric Video)-mg5Bp_Gzs0s.mp3
        # soundcloud downloads are named after the title of the song, followed by a dash and a random 9 digit unique ID
        # Eg. Curse the Weather-297150404.mp3
        song_title_regex = r".*" + re.escape(title) + r"-\S{9}(\S{2})?\.mp3"
        if url is not None:
            song_url_regex = r".*?-(" + re.escape(url[-11:]) + r").*"

        # find the downloaded file in the download folder and rename it to the proper name
        for file in os.listdir(filepath):
            if url is not None and re.match(song_url_regex, file):
                return file
            if re.match(song_title_regex, file):
                return file
        return None

    @staticmethod
    def write_metadata(song, filepath):
        """
        Takes a dictionary of song info and the filepath to the folder containing the song, and writes the metadata
        for Title, Artist, and Album to the song. The song must have been renamed first

        :param song: a dictionary of song info (must include fields for 'title', 'artist', 'album', and 'time')
        :param filepath: the filepath to the folder that contains the song
        :return: void
        """
        path_to_song = filepath + Util.get_song_filename(song)
        audio = Audio(path_to_song)
        audio.write_tags({
            "title": song["title"],
            "artist": song["artist"],
            "album": song["album"]
        })

        # access code preceded by 0o to represent octal number
        # Gives full read/write access to the song file, but not execute
        os.chmod(path_to_song, 0o666)

    @staticmethod
    def time_in_seconds(time):
        """
        Takes a String of the form xx:xx representing a time in minutes and seconds, and returns
        an int representing the time in seconds

        :param time: a String of the form xx:xx where the x's are ints
        :return: an int representing the time in seconds
        """
        mins = int(re.split(r":", time)[0])
        seconds = int(re.split(r":", time)[1])
        return mins * 60 + seconds

    @staticmethod
    def print_summary(stats, playlist_name):
        """
        Takes a list of ints representing download statistics and prints them to the console

        :param stats: a list of ints, where stats[0] is the number of requested songs, stats[1] is the number of songs
        that already existed, stats[2] is the number of songs that downloaded successfully, and
        stats[3] is a list of songs that failed to download
        :param playlist_name: the name of the playlist
        :return: void
        """
        print("\n===== Download Summary for \"{}\" =====".format(playlist_name))
        print("{} songs requested".format(stats[0]))
        print("{} songs already existed and were skipped".format(stats[1]))
        print("{} songs failed to download or were not found".format(stats[2]))
        print("{} songs were downloaded successfully".format(stats[3]))

    @staticmethod
    def check_file(filepath):
        """
        Checks if a file exists at filepath, and if not creates an empty file

        :param filepath: The path to a file
        :return: void
        """
        if not os.path.isfile(filepath):
            with open(filepath, "w") as file:
                file.write('\0')

    @staticmethod
    def normalize_audio(song_filepath):
        """
        Normalizes the audio of the song at filepath. Using ffmpeg-normalize this creates a new file, so the old
        one must be removed.

        :param song_filepath: the full filepath to the song
        :return: void
        """
        subprocess.run(["ffmpeg-normalize", "-u", "-p " + Util.NORMALIZED_SONG_PREFIX, "-l " + str(Util.NORMALIZED_RMS_DECIBELS), song_filepath])
        os.remove(song_filepath)
