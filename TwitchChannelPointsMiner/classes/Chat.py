import logging
import time
from enum import Enum, auto
from threading import Thread

from irc.bot import SingleServerIRCBot

from TwitchChannelPointsMiner.constants import IRC, IRC_PORT
from TwitchChannelPointsMiner.classes.Settings import Events, Settings

logger = logging.getLogger(__name__)


class ChatPresence(Enum):
    ALWAYS = auto()
    NEVER = auto()
    ONLINE = auto()
    OFFLINE = auto()

    def __str__(self):
        return self.name


class ClientIRC(SingleServerIRCBot):
    def __init__(self, username, token, channel):
        self.token = token
        self.channel = "#" + channel
        self.__active = False

        super(ClientIRC, self).__init__(
            [(IRC, IRC_PORT, f"oauth:{token}")], username, username
        )

    def on_welcome(self, client, event):
        client.join(self.channel)

    def start(self):
        self.__active = True
        self._connect()
        while self.__active:
            try:
                self.reactor.process_once(timeout=0.2)
                time.sleep(0.01)
            except Exception as e:
                logger.error(
                    f"Обнаружено исключение: {e}. Поток активен: {self.__active}"
                )

    def die(self, msg="Bye, cruel world!"):
        self.__active = False
        self.connection.disconnect(msg)

    """
    def on_join(self, connection, event):
        logger.info(f"Событие: {event}", extra={"emoji": ":speech_balloon:"})
    """

    # """
    def on_pubmsg(self, connection, event):
        msg = event.arguments[0]
        mention = None

        if Settings.disable_at_in_nickname is True:
            mention = f"{self._nickname.lower()}"
        else:
            mention = f"@{self._nickname.lower()}"

        # also self._realname
        # if msg.startswith(f"@{self._nickname}"):
        if mention != None and mention in msg.lower():
            # nickname!username@nickname.tmi.twitch.tv
            nick = event.source.split("!", 1)[0]
            # chan = event.target

            logger.info(f"{nick}: {msg}", extra={
                        "emoji": ":speech_balloon:", "event": Events.CHAT_MENTION})
        #nick = event.source.split("!", 1)[0]
        #if nick == '0_0ynn0_0':
            #logger.info(f"{nick}: {msg}", extra={
                        #"emoji": ":speech_balloon:", "event": Events.CHAT_MENTION})
    # """


class ThreadChat(Thread):
    def __deepcopy__(self, memo):
        return None

    def __init__(self, username, token, channel):
        super(ThreadChat, self).__init__()

        self.username = username
        self.token = token
        self.channel = channel

        self.chat_irc = None

    def run(self):
        self.chat_irc = ClientIRC(self.username, self.token, self.channel)
        logger.info(
            f"Подключение к чату {self.channel}", extra={"emoji": ":speech_balloon:", "event": Events.GAIN_FOR_WATCH_STREAK}
        )
        self.chat_irc.start()

    def stop(self):
        if self.chat_irc is not None:
            logger.info(
                f"Отключение от чата {self.channel}", extra={"emoji": ":speech_balloon:", "event": Events.STREAMER_OFFLINE}
            )
            self.chat_irc.die()
