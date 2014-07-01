import sys

class KeyMaps(object):
    default = [('w',        'forward'),
               ('a',        'left'),
               ('s',        'backward'),
               ('d',        'right'),
               ('space',    'fire')
               ]

class InputManager(object):
    def __init__(self, showbase, localplayer, client):
        self.key_map = {'left': 0
                      , 'right': 0
                      , 'forward': 0
                      , 'backward': 0
                      , 'fire': 0 
                      }
        showbase.accept('escape', sys.exit)
        for key,cmd in KeyMaps.default:
            showbase.accept(key, self.set_key, [cmd, 1])
            showbase.accept(key+"-up", self.set_key, [cmd, 0])
        self.local_player = localplayer

    def set_key(self, key, value):
        self.key_map[key] = value
        client.send(key, value)

    def update(self, dt):
        pass
        for mapping in KeyMaps.default:
            self.local_player.handle_command(mapping[1], self.key_map[mapping[1]])
