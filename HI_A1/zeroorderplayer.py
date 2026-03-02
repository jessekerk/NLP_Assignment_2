from __future__ import annotations

import math

from perudo import PerudoBid, PerudoPlayer, get_valid_perudo_bids  # noqa: F401


class ZeroOrderPlayer(PerudoPlayer):
    """Class implementing the T0M0 zero-order theory of mind player.
    Author: Jesse Kerkhof (j.j.kerkhof@student.rug.nl)"""

    def _comb(self, player_count: int, j: int) -> float:
        """Helper function that implements the shared body of the challenge and bid probabilities.

        Args:
            player_count (int): Integer representing the amount of players in the game.
            j (int): Iterator for loloping through the dice

        Returns:
            float: Float representing the likelihood that challenging / raising on this bid will result in success.
        """
        return (
            math.comb(5 * (player_count - 1), j)
            * (1 / 6) ** j
            * (5 / 6) ** (5 * (player_count - 1) - j)
        )

    def calculate_challenge_chance(
        self, dice: tuple[int], player_count: int, bid: PerudoBid | None
    ) -> float:
        """Function that calculates the likelihood that challenging on this bid will result in a success.

        Args:
            dice (tuple[int]): Tuple representing the held dice's count and face value.
            player_count (int): Integer representing the amount of players in the game.
            bid (PerudoBid | None): Custom class that represents the current bid. (None means that our agent takes the first bid).

        Returns:
            float: The chance that challenging this bid will result in a success.
        """
        challenge_loop_end = (
            bid.count - dice.count(bid.face_value)  # type: ignore
        )  # The top of the sigma at p_challenge formula

        bid_chance = 0
        for j in range(0, challenge_loop_end):
            bid_chance += self._comb(player_count, j)
        return bid_chance

    def calculate_bid_chance(
        self, dice: tuple[int], player_count: int, bid: PerudoBid | None
    ) -> float:
        """Function that calculates the likelihood that raising  this bid will result in a success.

        Args:
            dice (tuple[int]): Tuple representing the held dice's count and face value.
            player_count (int): Integer representing the amount of players in the game.
            bid (PerudoBid | None): Custom class that represents the current bid. (None means that our agent takes the first bid).

        Returns:
            float: The chance that raising this bid will result in a success.
        """
        bid_loop_start = max(0, bid.count - dice.count(bid.face_value))  # type: ignore
        bid_loop_end = 5 * (player_count - 1)

        bid_chance = 0

        for j in range(bid_loop_start, bid_loop_end):
            bid_chance += self._comb(player_count, j)
        return bid_chance

    def take_turn(
        self, dice: tuple[int], player_count: int, bid: PerudoBid | None
    ) -> PerudoBid | None:
        """Decide whether to raise the bid or challenge it.

        The method generates all valid bids that could legally follow the current bid.
        For each of those, it computes the probability that raising to that bid would be correct.
        It selects the bid with the highest probability.

        It then computes the probability that challenging the current bid would succeed.
        If the best challenge probability is at least as high as the best bid probability,
        the player challenges (returning None). Otherwise it returns the best next bid.

            Args:
                dice (tuple[int]): Tuple representing the held dice's count and face value.
                player_count (int): Integer representing the game's amoutn of players.
                bid (PerudoBid | None): The current bid the agent has to play with.

            Returns:
                PerudoBid | None: Either raises the bid and returns a PerudoBid, or challenges and returns None.
        """

        valid_bids = get_valid_perudo_bids(bid, player_count * 5)

        # Calculating raising chances
        best_bid = None
        best_bid_probability = 0.0

        for bid_option in valid_bids:
            bid_probability = self.calculate_bid_chance(dice, player_count, bid_option)
            if bid_probability > best_bid_probability:
                best_bid_probability = bid_probability
                best_bid = bid_option  # Calculates best bid in the list of valid bids

        # If the agent starts, bid the dice that maximizes the raising probability.
        if bid is None:
            return best_bid

        # Calculating challenging chance
        best_challenge_probability = self.calculate_challenge_chance(
            dice, player_count, bid
        )

        # Main choosing logic
        if best_challenge_probability >= best_bid_probability:
            return None  # Challenge the incoming bid
        else:
            return best_bid


# Decision
# if p_challenge >= p_bid(k, f), challenge
# if p_challenge < p_bid(k', f'), raise to (k', f')
# if agent does initial bid, bid k', f' that maximizes p_bid(k, f)

# Implement bid reading, then the formulas, then compare the probabilities, then decide and return the bid.
# k = bid.count
# f = bid.face_value
# k_f = dice.count(bid.face_value)
