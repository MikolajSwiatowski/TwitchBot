import socket
import datetime
import random
from collections import namedtuple

import config


TEMPLATE_COMMANDS = {
    '!discord': 'Please join the {message.channel} Discord server, {message.user}',
    '!so': 'Check out {message.text_args[0]}, they are a nice streamer!',
    '!instagram': 'Hey! Make sure to check out {message.channel} instagram on instagram.com',
    '!facebook': 'All latest information about streams can be checked on facebook.com !',
    '!youtube': 'Join the {message.channel} youtube channel here: youtube.com',
}


Message = namedtuple(
    'Message',
    'prefix user channel irc_command irc_args text text_command text_args',
)



class Bot:
    def __init__(self):
        self.irc_server = 'irc.twitch.tv'
        self.irc_port = 6667
        self.oauth_token = config.OAUTH_TOKEN
        self.username = 'DavardoServant'
        self.channels = ['leondavardo']
        self.custom_commands = {
            '!date': self.reply_with_date,
            '!ping': self.reply_to_ping,
            '!randint': self.reply_with_randint,
            'hey': self.reply_to_hey,
            'hi': self.reply_to_hey,
            '!pokeball': self.reply_to_pokeball,
            '!pokedex': self.reply_to_pokedex,
            '!love': self.reply_to_lovemeter,
        }

    def send_command(self, command):
        if 'PASS' not in command:
            print(f'< {command}')
        self.irc.send((command + '\r\n').encode())

    def send_privmsg(self, channel, text):
        self.send_command(f'PRIVMSG #{channel} :{text}')


    def connect(self):
        self.irc = socket.socket()
        self.irc.connect((self.irc_server, self.irc_port))
        self.send_command(f'PASS {self.oauth_token}')
        self.send_command(f'NICK {self.username}')
        for channel in self.channels:
            self.send_command(f'JOIN #{channel}')
            self.send_privmsg(channel, 'Bot succesfully joined the channel!')
        self.loop_for_messages()





    def get_user_from_prefix(self, prefix):
        domain = prefix.split('!')[0]
        if domain.endswith('.tmi.twitch.tv'):
            return domain.replace('.tmi.twitch.tv', '')
        if 'tmi.twitch.tv' not in domain:
            return domain
        return None

    def parse_message(self, received_msg):
        parts = received_msg.split(' ')

        prefix = None
        user = None
        channel = None
        text = None
        text_command = None
        text_args = None
        irc_command = None
        irc_args = None

        if parts[0].startswith(':'):
            prefix = parts[0][1:]
            user = self.get_user_from_prefix(prefix)
            parts = parts[1:]

        text_start = next(
            (idx for idx, part in enumerate(parts) if part.startswith(':')),
            None
        )
        if text_start is not None:
            text_parts = parts[text_start:]
            text_parts[0] = text_parts[0][1:]
            text = ' '.join(text_parts)
            text_command = text_parts[0]
            text_args = text_parts[1:]
            parts = parts[:text_start]

        irc_command = parts[0]
        irc_args = parts[1:]

        hash_start = next(
            (idx for idx, part in enumerate(irc_args) if part.startswith('#')),
            None
        )
        if hash_start is not None:
            channel = irc_args[hash_start][1:]

        message = Message(
            prefix=prefix,
            user=user,
            channel=channel,
            text=text,
            text_command=text_command,
            text_args=text_args,
            irc_command=irc_command,
            irc_args=irc_args,
        )

        return message

    def handle_template_command(self, message, text_command, template):
        text = template.format(**{'message': message})
        self.send_privmsg(message.channel, text)

    def reply_with_date(self, message):
        formatted_date = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
        text = f'Here you go {message.user}, the date is: {formatted_date}.'
        self.send_privmsg(message.channel, text)

    def reply_to_ping(self, message):
        text = f'Hey {message.user}, nice ping! PONG!'
        self.send_privmsg(message.channel, text)

    def reply_to_hey(self, message):
        text = f'Hey {message.user}, how you doin?'
        self.send_privmsg(message.channel, text)



    def reply_to_pokeball(self, message):
        pokemons_file = open("pokemons.txt")
        lines_to_read = [random.randint(0,151)]

        for position, line in enumerate(pokemons_file):
            if position in lines_to_read:
                text = f'Congratulations! you just caught #{line} !'
                self.send_privmsg(message.channel, text)


    def reply_to_lovemeter(self, message):
        lovemeter = random.randint(0,100)
        if(lovemeter < 25):
            text = f'Oof not too much love between {message.user} and {message.text_args[0]} only {lovemeter}% StinkyGlitch '
            self.send_privmsg(message.channel, text)
        elif(lovemeter >= 25 and lovemeter <= 75):
            text = f'There is {lovemeter}% love beetwen {message.user} and {message.text_args[0]} <3 '
            self.send_privmsg(message.channel, text)
        elif(lovemeter > 75):
            text = f'Sheeeesh LOVE IS IN THE AIR! There is {lovemeter}% love beetwen {message.user} and {message.text_args[0]} TwitchUnity '
            self.send_privmsg(message.channel, text)



    def reply_to_pokedex(self, message):
            get_pokemon = message.text_args[0]

            self.send_privmsg(message.channel, get_pokemon)
            #veryfing correct input



    def reply_with_randint(self, message):
        text = str(random.randint(0, 1000))
        self.send_privmsg(message.channel, text)

    def handle_message(self, received_msg):
        if len(received_msg) == 0:
            return


        message = self.parse_message(received_msg)
        print(f'> {message}')

        if message.irc_command == 'PING':
            self.send_command('PONG :tmi.twitch.tv')

        if message.irc_command == 'PRIVMSG':
            if message.text_command in TEMPLATE_COMMANDS:
                self.handle_template_command(
                    message,
                    message.text_command,
                    TEMPLATE_COMMANDS[message.text_command],
                )
            if message.text_command in self.custom_commands:
                self.custom_commands[message.text_command](message)

    def loop_for_messages(self):
        while True:
            received_msgs =""
            received_msgs = received_msgs + self.irc.recv(2048).decode()
            for received_msg in received_msgs.split('\r\n'):
                self.handle_message(received_msg)



def main():
    bot = Bot()
    bot.connect()







if __name__ == '__main__':
    main()