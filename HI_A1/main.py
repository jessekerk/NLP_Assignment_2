from firstorderplayer import FirstOrderPlayer
from perudo import Perudo
from randomplayer import RandomPlayer  # noqa: F401
from zeroorderplayer import ZeroOrderPlayer

game = Perudo()
game.join(FirstOrderPlayer())
game.join(ZeroOrderPlayer())

game.play(debug=True)
print(game.repeated_games(1000))
