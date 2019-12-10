from enum import Enum, unique

import discord
import regex

default_message_metadata = dict(
    expire_time=None,
    created_at=None,
    message_id=None,
    message_channel_id=None,
    category_id=None,
    webhook_id=None,
)


BOT_STATUS = [discord.Status.online, discord.Status.idle, discord.Status.do_not_disturb]
BOT_ACTIVITY_CKS = {
    "5395225192883814521345": discord.Activity(
        type=discord.ActivityType.streaming,
        url="https://www.twitch.tv/malvinarum",
        name="Malvinarum",
    ),
    "5395225192883814523536": discord.Activity(
        type=discord.ActivityType.streaming,
        url="https://www.twitch.tv/noobk1lla",
        name="N0obkilla",
    ),
}
BOT_ACTIVITY_PHONOS = {
    "5395225192883814521345": discord.Activity(
        type=discord.ActivityType.watching, name="Over the best server ever"
    ),
    "5395225192883814523536": discord.Game(name="with the strings of reality"),
}


def get_bot_activity_cks():
    global BOT_ACTIVITY_CKS
    return BOT_ACTIVITY_CKS


def set_bot_activity_cks(activity):
    global BOT_ACTIVITY_CKS
    BOT_ACTIVITY_CKS = activity


def get_bot_activity_phonos():
    global BOT_ACTIVITY_PHONOS
    return BOT_ACTIVITY_PHONOS


def set_bot_activity_phonos(activity):
    global BOT_ACTIVITY_PHONOS
    BOT_ACTIVITY_PHONOS = activity


CONTINENT_DATA = {
    "1": "Europe",
    "2": "Africa",
    "3": "North America",
    "4": "Asia",
    "5": "Oceania",
    "6": "South America",
}
TIMEZONE_REGEX = regex.compile("UTC[+-]([01]\d|2[0-4])(:?[0-5]\d)?|UTC[+-]\d", regex.I)

UNITS = {"s": "seconds", "m": "minutes", "h": "hours", "d": "days", "w": "weeks"}
REPLACE_BRACKER = regex.compile(r"\((?:[^()]++|(?R))*+\)")
NAMEFIXER = regex.compile(
    "^[\p{Punctuation}\p{Symbol}\p{Letter_Number}\p{Other_Number}\p{Punctuation}\p{Mark}\p{Separator}]*"
)
QUOTE_CLEANER = regex.compile(
    "^(<+[\p{P}\p{Sm}\p{Sc}\p{Sk}\p{So}\p{M}\p{Z}\p{N}]*>+)*$|^(:+[\p{P}\p{Sm}\p{Sc}\p{Sk}\p{So}\p{M}\p{Z}\p{N}\p{L}]*:+)*$|^([:<]+[\p{L}\p{N}\p{P}]+[:>]+)+$",
    regex.I | regex.M,
)
URLMATCHER = regex.compile(
    "(?:(?:https?|ftp)://|\b(?:[a-z\d]+.))(?:(?:[^\s()<>]+|((?:[^\s()<>]+|(?:([^\s()<>]+)))?))+(?:((?:[^\s()<>]+|(?:(?:[^\s()<>]+)))?)|[^\s`!()[]{};:'\".,<>?«»“�?‘’]))?",
    regex.I,
)
RED = 0xFF2828
GREEN = 0x28FF5A
BLUE = 0x2876FF


class MessageTypes(Enum):
    ERROR = 0xDC0000
    WARNING = 0xE54F03
    SUCCESS = 0x03FB00
    INFO = 0x0A24CB
    QUESTION = 0x8A2BE2
    DEFAULT = 0x2893FF

    @classmethod
    def get_colour(cls, message_type):
        """Get Appropriate colour for message type"""
        if message_type:
            if message_type.lower() == "error":
                return discord.Colour(cls.ERROR.value)
            elif message_type.lower() == "success":
                return discord.Colour(cls.SUCCESS.value)
            elif message_type.lower() == "warn":
                return discord.Colour(cls.WARNING.value)
            elif message_type.lower() == "info":
                return discord.Colour(cls.INFO.value)
            elif message_type.lower() == "question":
                return discord.Colour(cls.QUESTION.value)
        return discord.Colour(cls.DEFAULT.value)


bfv_icon = (
    "https://cdn.discordapp.com/app-icons/512699108809637890/5f70bb592b9efbad9b5973404b9b7d01.png"
)
anthem_icon = (
    "https://cdn.discordapp.com/app-icons/546175179542364160/4a0b14af7ed47532e7e4676b637bdf3f.png"
)
apex_icon = (
    "https://cdn.discordapp.com/app-icons/542075586886107149/7564e6f23704870d70480f172f127677.png"
)
spotify_icon = "https://upload.wikimedia.org/wikipedia/commons/thumb/2/26/Spotify_logo_with_text.svg/559px-Spotify_logo_with_text.svg.png"
division_2_icon = (
    "https://cdn.discordapp.com/app-icons/554921822626381879/aadb17a9cb43c0d24bd270406fecb87d.png"
)
osrs_icon = (
    "https://cdn.discordapp.com/app-icons/357606832899883008/337ce51307d4580001d1ab60706dda8a.png"
)
csgo_icon = (
    "https://cdn.discordapp.com/app-icons/356875057940791296/782a3bb612c6f1b3f7deed554935f361.png"
)
lol_icon = "https://cdn.discordapp.com/app-assets/401518684763586560/416719019576393738.png"
minecraft_icon = (
    "https://cdn.discordapp.com/app-icons/356875570916753438/166fbad351ecdd02d11a3b464748f66b.png"
)
codmw_icon = "https://cdn.discordapp.com/attachments/557869681721999370/637186507475779585/communityIcon_8jyqgoe3xk131.png"

POLL_CONFIG = dict(
    poll_id=None,
    channel_id=None,
    guild_id=None,
    created_by=None,
    created_time=None,
    question=None,
    deletion_timer=None,
    single_vote=True,
    voters=[],
    op1=None,
    op1Score=None,
    op2=None,
    op2Score=None,
    op3=None,
    op3Score=None,
    op4=None,
    op4Score=None,
    op5=None,
    op5Score=None,
    op6=None,
    op6Score=None,
    op7=None,
    op7Score=None,
    op8=None,
    op8Score=None,
    op9=None,
    op9Score=None,
)


def enable_get(attribute):
    def _enable_get(f):  # @UnusedVariable
        def wrapper(self, *args):  # @UnusedVariable
            return getattr(self, attribute)

        return wrapper

    return _enable_get


@unique
class Roles(Enum):
    community_leader = "Community Leader"
    council = "Council"
    game_leader = "Game Leader"
    media_team = "Media Team"
    community_veteran = "Community Veteran"
    community_member = "Community Member"
    community_trial = "Community Trial"
    guest = "Guest"
    rainbow = "RGB"

    admin = "Admins"
    senior_moderator = "Senior Moderator"
    moderator = "Moderator"
    phonos_not_streamer = "Lurker (LVL1)"
    member = "Members"
    VIP = "VIP"
    staff = "Staff"

    streaming = "Streaming"
    streamer = "Streamer"
    on_voice = "on-voice"
    bots = "Bots"
    muted = "Muted"

    machine_overlord = "Machine Overlord"

    has_profile = "Has profile"
    no_profile = "Doesn't have profile"

    @classmethod
    def get(self):
        return self.value

    @classmethod
    def get_staff(cls):
        # cls here is the enumeration
        return cls.staff.value

    @classmethod
    def get_admins(cls):
        # cls here is the enumeration
        return cls.admin.value

    @classmethod
    def get_phonos_not_streamer(cls):
        # cls here is the enumeration
        return cls.phonos_not_streamer.value

    @classmethod
    def get_senior_moderator(cls):
        # cls here is the enumeration
        return cls.senior_moderator.value

    @classmethod
    def get_moderators(cls):
        # cls here is the enumeration
        return cls.moderator.value

    @classmethod
    def get_vip(cls):
        # cls here is the enumeration
        return cls.VIP.value

    @classmethod
    def get_members(cls):
        # cls here is the enumeration
        return cls.member.value

    @classmethod
    def get_bots(cls):
        # cls here is the enumeration
        return cls.bots.value

    @classmethod
    def get_has_profile(cls):
        # cls here is the enumeration
        return cls.has_profile.value

    @classmethod
    def get_no_profile(cls):
        # cls here is the enumeration
        return cls.no_profile.value

    @classmethod
    def get_muted(cls):
        # cls here is the enumeration
        return cls.muted.value

    @classmethod
    def get_community_leader(cls):
        return cls.community_leader.value

    @classmethod
    def get_council(cls):
        return cls.council.value

    @classmethod
    def get_game_leader(cls):
        return cls.game_leader.value

    @classmethod
    def get_community_veteran(cls):
        return cls.community_veteran.value

    @classmethod
    def get_trial(cls):
        return cls.community_trial.value

    @classmethod
    def get_community_member(cls):
        return cls.community_member.value

    @classmethod
    def get_voice(cls):
        return cls.on_voice.value

    @classmethod
    def get_streamer(cls):
        return cls.streamer.value

    @classmethod
    def get_guest(cls):
        return cls.guest.value

    @classmethod
    def get_rainbow(cls):
        return cls.rainbow.value

    @classmethod
    def get_streaming(cls):
        return cls.streaming.value


@unique
class Channels(Enum):
    bot_status = "bot-status"

    @classmethod
    def get(self):
        return self.value

    @classmethod
    def get_bot_status(cls):
        # cls here is the enumeration
        return cls.bot_status.value


@unique
class Emoji(Enum):
    streaming = "\U0001F3A5"
    eyes = "\U0001F440"
    heart = "\u2764"
    evil_face = "\U0001F608"
    middle_finger = "\U0001F595"
    spy = "\U0001F575"

    def __str__(self):
        return str(self.value)

    @enable_get("value")
    def get(self):
        pass
