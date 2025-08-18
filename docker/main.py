import json
import os
import subprocess
import tempfile

from datetime import datetime
from typing import Any

from dotenv import load_dotenv
from loguru import logger
from pydantic import BaseModel
from twitch import TwitchHelix


load_dotenv()
client_id = os.environ.get("TWITCH_API_CLIENT_ID", None)
client_secret = os.environ.get("TWITCH_API_CLIENT_SECRET", None)
twitch_downloader_path = os.environ.get(
    "TWITCH_DOWNLOADER_PATH", "./TwitchDownloaderCLI"
)
emote_stats_path = os.environ.get("EMOTE_STAT_JSON", "../src/public/emote-stats.json")
emote_stats_config = os.environ.get("EMOTE_STAT_CONFIG", "config.json")


class VodInfo(BaseModel):
    id: str
    title: str
    created: datetime
    published: datetime


class EmoteUser(BaseModel):
    display_name: str
    use_index: int = 0


class EmoteInfo(BaseModel):
    name: str
    users: list[EmoteUser] = []


class VodEmoteStat(BaseModel):
    info: VodInfo
    emotes: list[EmoteInfo]


class EmoteStateContainer(BaseModel):
    data: dict[str, VodEmoteStat] = {}


def fetch_current_data(json_path: str):
    if not os.fie.exists(json_path):
        raise FileNotFoundError("Provided JSON path not found")

    with open(json_path, "r") as f:
        data = json.load(f)

    return data


def get_current_vods(channel_name: str) -> list[VodInfo]:
    """Gets list of vods that presently exist for user

    Args:
        channel_name (str): Channel display name

    Returns:
        list[VodInfo]: List of Vods
    """
    client_helix = TwitchHelix(client_id=client_id, client_secret=client_secret)
    client_helix.get_oauth()
    user_info = client_helix.get_users(login_names=[channel_name])[0]
    channel_id = user_info["id"]

    vid_iter = client_helix.get_videos(user_id=channel_id, page_size=100)
    stream = client_helix.get_streams(user_ids=channel_id)
    if len(stream) == 1:  # Skip first vod ID if
        next(vid_iter)

    vod_list: list[VodInfo] = []
    for video in vid_iter:
        vod = VodInfo(
            id=video["id"],
            title=video["title"],
            created=video["created_at"],
            published=video["published_at"],
        )
        vod_list.append(vod)
    return vod_list


def get_chat_json(vod_id: str) -> dict[str, Any]:
    """Uses twitch download CLI to pull chat JSON for specific VOD ID

    Args:
        vod_id (str): VOD ID

    Returns:
        dict[str, Any]: Downloaded JSON object
    """
    data = None
    with tempfile.TemporaryDirectory() as tmpdirname:
        # https://github.com/lay295/TwitchDownloader?tab=readme-ov-file#cli
        temp_json = os.path.join(tmpdirname, f"chat_logs_{vod_id}.json")
        cmd = (
            twitch_downloader_path
            + " chatdownload --collision Overwrite"
            + f" --id {vod_id}"
            + " --chat-connections 6"
            + " --bttv false --ffz false --stv false"
            + f' -o "{temp_json}"'
        )
        print(cmd)
        subprocess.Popen(cmd, shell=True).wait()
        with open(temp_json, "r", encoding="utf8") as f:
            data = json.load(f)

    return data


def get_emote_users(
    chat_json: dict[str, Any], emote_names: list[str]
) -> list[EmoteInfo]:
    emote_info = []
    for emote_name in emote_names:
        logger.info(
            f"Searching for emote {emote_name} in vod {chat_json['video']['id']}"
        )
        emote_users: dict[str, EmoteUser] = {}
        for comment in chat_json["comments"]:
            # First check if subscriber and if not skip
            # sub = False
            # for badge in comment['message']['user_badges']:
            #     if badge["_id"] == "subscriber":
            #         sub = True
            #         break
            # if not sub and sub_only:
            #     continue
            # Look for emote in body
            if emote_name in comment["message"]["body"]:
                commenter = comment["commenter"]["display_name"]
                if commenter in emote_users:
                    emote_users[commenter].use_index += 1
                else:
                    emote_users[commenter] = EmoteUser(
                        display_name=commenter, use_index=1
                    )

        emote_info.append(EmoteInfo(name=emote_name, users=list(emote_users.values())))

    return emote_info


if __name__ == "__main__":
    with open(emote_stats_config, "r", encoding="utf-8") as file:
        emote_config = json.load(file)

    if emote_stats_path:
        with open(emote_stats_path, "r", encoding="utf-8") as file:
            emote_stats = json.load(file)
        emote_stats = EmoteStateContainer.model_validate(emote_stats)
    else:
        emote_stats = EmoteStateContainer()

    vod_list = get_current_vods(emote_config["channel_name"])
    updated = False
    # Loop over vods
    for vod in vod_list:
        # Skip if already in stat JSON
        if vod.id in emote_stats.data:
            logger.info(f"VOD id {vod.id} already in json")
            continue

        logger.warning(f"VOD id {vod.id} is new")
        chat_data = get_chat_json(vod.id)
        # with open("raw_output.json", "w") as file:
        #     json.dump(chat_data, file)

        emote_info = get_emote_users(
            chat_data,
            emote_config["emotes"],
        )
        emote_stats.data[vod.id] = VodEmoteStat(info=vod, emotes=emote_info)
        logger.success("VOD emote information parsed")

    if updated:
        with open(emote_stats_path, "w", encoding="utf-8") as file:
            file.write(emote_stats.model_dump_json(indent=2))
        logger.success("VOD stat json updated")
    else:
        logger.success("No new VODs, carry on :)")
