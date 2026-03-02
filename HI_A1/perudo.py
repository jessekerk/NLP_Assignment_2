from __future__ import annotations

import random


class PerudoBid:
    """
    Represents a bid in the Perudo game, containing
    a count of a given face_value
    """

    def __init__(self, count: int, face_value: int):
        self.count = count
        self.face_value = face_value

    def __str__(self):
        return str(self.count) + " dice showing a " + str(self.face_value)

    def __eq__(self, other):
        if isinstance(other, PerudoBid):
            return self.face_value == other.face_value and self.count == other.count
        return False

    def __gt__(self, other):
        if isinstance(other, PerudoBid):
            if self.count != other.count:
                return self.count > other.count
            return self.face_value > other.face_value
        return False


class PerudoPlayer:
    """
    Abstract class for a Perudo player
    """

    def start_game(self, identifier: int, dice: tuple[int]):
        """
        Signals the start of the game, and passes the agent their identifier.
        :param identifier: integer identifier of the agent
        :param dice: tuple of the dice throws of the agent
        """
        pass

    def take_turn(
        self, dice: tuple[int], player_count: int, bid: PerudoBid | None
    ) -> PerudoBid | None:
        """
        Requests the player to take their turn
        :param dice: tuple of face values the player has thrown
        :param player_count: total number of players in the game (including the current player)
        :param bid: PerudoBid made by the previous player, or None on the first bid
        :return: PerudoBid that raises the last bid, or None on a challenge
        """
        return None

    def observe_bid(self, bid: PerudoBid, player: int) -> None:
        """
        Passes an observation of a bid to the player. This is performed for
        all bids, including the bid that player will be asked to react to
        :param bid: PerudoBid that was made
        :param player: identifier of the player that made the bid
        :return: None
        """
        pass

    def observe_challenge(self, bid: PerudoBid, player: int, success: bool) -> None:
        """
        Passes an observation of a challenged bid to the player
        :param bid: PerudoBid that was challenged
        :param player: identifier of the player that issued the challenge
        :param success: boolean indicating whether the challenge was successful
                        (i.e. whether the bid was unsuccessful)
        :return: None
        """
        pass


class Perudo:
    """
    Implementation of a game of Perudo
    """

    DICE_PER_PLAYER = 5

    def __init__(self):
        self._players = []

    def join(self, player: PerudoPlayer) -> None:
        """
        Has a player join the game at the end of the turn order
        :param player: PerudoPlayer that joins the game
        """
        if player not in self._players:
            self._players.append(player)

    def play(
        self,
        *,
        debug: bool = False,
        challenge_win_score: int = 1,
        challenge_lose_score: int = -1,
        bid_win_score: int = 1,
        bid_lose_score: int = -1,
    ) -> list[int]:
        """
        Plays a single Perudo game
        :param debug: flag to display debug messages, default False
        :return: list that indicates who lost (-1) and who won (+1) the game
        """
        if len(self._players) < 1:
            raise ValueError("Game has no players")
        dice = [
            tuple(sorted([random.randint(1, 6) for _ in range(self.DICE_PER_PLAYER)]))
            for player in self._players
        ]
        score = [0 for _ in self._players]
        for player in range(len(self._players)):
            self._players[player].start_game(player, dice[player])
        if debug:
            for player in range(len(self._players)):
                print("Player", player, "rolled", dice[player])
        current_player = 0
        current_bid = self._players[current_player].take_turn(
            dice[current_player], len(self._players), None
        )
        while current_bid is not None:
            if debug:
                print("Player", current_player, "bid", current_bid)
            for player in self._players:
                player.observe_bid(current_bid, current_player)
            current_player = (current_player + 1) % len(self._players)
            old_bid = current_bid
            current_bid = self._players[current_player].take_turn(
                dice[current_player], len(self._players), old_bid
            )
            if current_bid is None or not current_bid > old_bid:
                break
        if current_bid is None:
            if debug:
                print("Player", current_player, "challenged the bid")
            count = 0
            for player_dice in dice:
                for die in player_dice:
                    if die == old_bid.face_value:  # type: ignore
                        count += 1
            if count >= old_bid.count:  # type: ignore
                score[current_player] = challenge_lose_score
                score[(current_player - 1)] = bid_win_score
                if debug:
                    print("Player", current_player, "failed the challenge")
            else:
                score[current_player] = challenge_win_score
                score[current_player - 1] = bid_lose_score
                if debug:
                    print("Player", current_player, "challenged succesfully")
            for player in self._players:
                player.observe_challenge(old_bid, current_player, count < old_bid.count)  # type: ignore
        elif debug:
            print("Player", current_player, "made invalid bid", current_bid)
            score[current_player] = challenge_lose_score
        return score

    def repeated_games(
        self,
        number_of_games: int,
        *,
        challenge_win_score: int = 1,
        challenge_lose_score: int = 0,
        bid_win_score: int = 1,
        bid_lose_score: int = 0,
    ) -> list[int]:
        """
        Performs a series of games
        :param number_of_games: number of games to perform
        :return: total number of wins for each player across games
        """
        total_score = [0 for _ in range(len(self._players))]
        for _ in range(number_of_games):
            score = self.play(
                challenge_win_score=challenge_win_score,
                challenge_lose_score=challenge_lose_score,
                bid_win_score=bid_win_score,
                bid_lose_score=bid_lose_score,
            )
            for player in range(len(score)):
                total_score[player] += score[player]
        return total_score


def get_valid_perudo_bids(
    bid: PerudoBid | None = None, dice_count: int = 10
) -> list[PerudoBid]:
    if bid is None:
        bid = PerudoBid(1, 0)
    valid_bids = []
    for count in range(1, dice_count + 1):
        for face in range(1, 7):
            if PerudoBid(count, face) > bid:
                valid_bids.append(PerudoBid(count, face))
    return valid_bids
