import random

from perudo import Perudo, PerudoBid, PerudoPlayer


class RandomPlayer(PerudoPlayer):
    def take_turn(self, dice: tuple[int], player_count: int, bid: PerudoBid|None) -> PerudoBid|None:
        valid_bids = []
        if bid is None:
            bid = PerudoBid(1, 0)
        else:
            valid_bids = [None]
        for face in range(bid.face_value + 1, 7):
            valid_bids.append(PerudoBid(bid.count, face))   #type: ignore
        for count in range(bid.count + 1, (player_count - 1) * Perudo.DICE_PER_PLAYER + 1):
            for face in range(1, 7):
                valid_bids.append(PerudoBid(count, face))   #type: ignore
        return random.choice(valid_bids)


    def observe_outcome(self, bid: PerudoBid, success: bool) -> None:
        pass