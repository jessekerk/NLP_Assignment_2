
        
def oldfunc():
            for dice in list(self.initial_beliefs.keys()):
            incoming_bid_chance = ZeroOrderPlayer().calculate_bid_chance(
                dice, player_count=2, bid=self.previous_bid
            )
            if bid == incoming_bid_chance:
                beta += self.initial_beliefs[dice]
            else:
                self.initial_beliefs[dice] = 0

        for dice_key in list(self.initial_beliefs.keys()):
            if beta != 0.0:
                self.initial_beliefs[dice_key] /= beta
        self.updated_beliefs = dict(self.initial_beliefs)


from __future__ import annotations

import itertools
import math

from perudo import PerudoBid, PerudoPlayer, get_valid_perudo_bids  # noqa: F401
from zeroorderplayer import ZeroOrderPlayer


class FirstOrderPlayer(PerudoPlayer):
    """Class implementing the first order theory of mind logic for a perudo agent.
    Author: Jesse Kerkhof (j.j.kerkhof@student.rug.nl)
    """

    def _world_to_dice(self, k_tuple: tuple[int]) -> tuple[int]:
        dice_list = []
        for face in range(1, 7):
            count = k_tuple[face - 1]
            for _ in range(count):
                dice_list.append(face)
        return tuple(dice_list)

    def start_game(self, identifier: int, dice: tuple[int]) -> None:
        """Function that starts the game if the ToM1 agent has to start.

        Args:
            identifier (int): integer identifier of the agent.
            dice (tuple[int]): tuple of the dice throws of the agent.

        Returns:
            beliefs:
        """
        # Calculate total dice in the game; assumes self.player_count is set elsewhere
        if not hasattr(self, "player_count"):
            self.player_count = 2
        total_dice_opponent = (self.player_count - 1) * 5

        self.initial_beliefs = {}
        self.my_dice = dice

        for k_tuple in itertools.product(range(total_dice_opponent + 1), repeat=6):
            if sum(k_tuple) == total_dice_opponent:
                numerator = math.factorial(total_dice_opponent)
                denominator = math.prod(math.factorial(k) for k in k_tuple)
                prob = (numerator / denominator) * ((1 / 6) ** total_dice_opponent)
                self.initial_beliefs[k_tuple] = prob
        self.previous_bid = None

    def observe_bid(self, bid: PerudoBid, player: int) -> None:
        # take 0 order agent, ask them what if they hold this dice and make this bid, what would they do
        if self.previous_bid is None:
            self.previous_bid = bid
            return None

        beta = 0.0

        for k_tuple in list(self.initial_beliefs.keys()):
            hypothetical_dice = self._world_to_dice(k_tuple)

            incoming_bid_chance = ZeroOrderPlayer().calculate_bid_chance(
                hypothetical_dice, player_count=2, bid=self.previous_bid
            )

            self.initial_beliefs[k_tuple] *= incoming_bid_chance
            beta += self.initial_beliefs[k_tuple]

        if beta > 0:
            for k_tuple in self.initial_beliefs:
                self.initial_beliefs[k_tuple] /= beta

        self.updated_beliefs = dict(self.initial_beliefs)
        self.previous_bid = bid

    def observe_challenge(self, bid: PerudoBid, player: int, success: bool) -> None:
        pass

    def calculate_expected_value_challenge(
        self, dice: tuple[int], player_count: int, bid: PerudoBid | None
    ) -> float:  # type: ignore
        win_probability = 0
        lose_probability = 0

        opponent_kf = k_tuple[bid.face_value - 1]
        
        for dice.count(bid.face_value) + 
    
    
    
    
    def calculate_expected_value_bid(
        self, dice: tuple[int], player_count: int, bid: PerudoBid | None
    ) -> float:  # type: ignore
        expected_bid_chance = 1
        return expected_bid_chance

    def take_turn(
        self, dice: tuple[int], player_count: int, bid: PerudoBid | None
    ) -> PerudoBid | None:
        expected_value_challenge = self.calculate_expected_value_challenge(
            dice, player_count, bid
        )
        expected_value_bid = self.calculate_expected_value_bid(dice, player_count, bid)
        if expected_value_challenge >= expected_value_bid:
            return None
        else:
            return PerudoBid(1, 0)  # Raise to k*, f*
        # Requirement: If the ToM1 agent is asked to make the initial bid, make the bid (k*, f*) that maximizes EV(1)bid(k*, f*)


# TODO: Update world initialization so its faster



from __future__ import annotations

import itertools
import math

from perudo import PerudoBid, PerudoPlayer, get_valid_perudo_bids  # noqa: F401
from zeroorderplayer import ZeroOrderPlayer


class FirstOrderPlayer(PerudoPlayer):
    """Class implementing the first order theory of mind logic for a perudo agent.
    Author: Jesse Kerkhof (j.j.kerkhof@student.rug.nl)
    """

    def _world_to_dice(self, k_tuple: tuple[int]) -> tuple[int]:
        dice_list = []
        for face in range(1, 7):
            count = k_tuple[face - 1]
            for _ in range(count):
                dice_list.append(face)
        return tuple(dice_list)

    def start_game(self, identifier: int, dice: tuple[int]) -> None:
        """Function that starts the game if the ToM1 agent has to start.

        Args:
            identifier (int): integer identifier of the agent.
            dice (tuple[int]): tuple of the dice throws of the agent.

        Returns:
            beliefs:
        """
        # Calculate total dice in the game; assumes self.player_count is set elsewhere
        if not hasattr(self, "player_count"):
            self.player_count = 2
        total_dice_opponent = (self.player_count - 1) * 5

        self.initial_beliefs = {}
        self.my_dice = dice

        for k_tuple in itertools.product(range(total_dice_opponent + 1), repeat=6):
            if sum(k_tuple) == total_dice_opponent:
                numerator = math.factorial(total_dice_opponent)
                denominator = math.prod(math.factorial(k) for k in k_tuple)
                prob = (numerator / denominator) * ((1 / 6) ** total_dice_opponent)
                self.initial_beliefs[k_tuple] = prob
        self.previous_bid = None

    def observe_bid(self, bid: PerudoBid, player: int) -> None:
        # take 0 order agent, ask them what if they hold this dice and make this bid, what would they do
        if self.previous_bid is None:
            self.previous_bid = bid  # Possibly unnecessary
            return None

        beta = 0.0

        for k_tuple in list(self.initial_beliefs.keys()):
            hypothetical_dice = self._world_to_dice(k_tuple)

            incoming_bid_chance = ZeroOrderPlayer().calculate_bid_chance(
                hypothetical_dice, player_count=2, bid=self.previous_bid
            )

            self.initial_beliefs[k_tuple] *= incoming_bid_chance
            beta += self.initial_beliefs[k_tuple]

        if beta > 0:
            for k_tuple in self.initial_beliefs:
                self.initial_beliefs[k_tuple] /= beta

        self.updated_beliefs = dict(self.initial_beliefs)
        self.previous_bid = bid

    def observe_challenge(self, bid: PerudoBid, player: int, success: bool) -> None:
        pass

    def calculate_expected_value_challenge(
        self, player_count: int, bid: PerudoBid
    ) -> float:
        win_prob = 0.0
        lose_prob = 0.0

        # Iterate over belief worlds
        for k_tuple, belief in self.initial_beliefs.items():
            # Opponent's dice showing bid.face_value
            opponent_kf = k_tuple[bid.face_value - 1]

            # How many we contribute
            my_kf = self.my_dice.count(bid.face_value)

            # Check if the opponent provides enough to reach bid.count
            if opponent_kf + my_kf < bid.count:
                win_prob += belief
            else:
                lose_prob += belief

        return win_prob - lose_prob

    # k = bid.count
    # f = bid.face_value
    # How many dice of this face do WE have?
    # my_kf = self.my_dice.count(f)

    def calculate_expected_value_bid(self, player_count: int, bid: PerudoBid) -> float:
        win_prob = 0.0
        lose_prob = 0.0

        for k_tuple, belief in self.initial_beliefs.items():
            hypothetical_dice = self._world_to_dice(k_tuple)

            opponent_kf = k_tuple[bid.face_value - 1]
            my_kf = self.my_dice.count(bid.face_value)

            # Probability that a TO-0 agent CHALLENGES the bid (k,f)
            p_challenge = ZeroOrderPlayer().calculate_challenge_chance(
                hypothetical_dice, player_count, bid
            )

            # CASE 1: Bid is TRUE in this world -> we WIN a challenge
            if opponent_kf + my_kf >= bid.count:
                win_prob += belief * p_challenge

            # CASE 2: Bid is FALSE in this world -> we LOSE a challenge
            else:
                lose_prob += belief * p_challenge

        return win_prob - lose_prob

    def take_turn(
        self, dice: tuple[int], player_count: int, bid: PerudoBid | None
    ) -> PerudoBid | None:
        # CASE 1 — We start the game (no previous bid)
        if bid is None:
            best_ev = float("-inf")
            best_bid = None

            for next_bid in get_valid_perudo_bids(None, player_count * 5):
                ev = self.calculate_expected_value_bid(player_count, next_bid)
                if ev > best_ev:
                    best_ev = ev
                    best_bid = next_bid

            return best_bid

        # CASE 2 — We respond to an incoming bid
        ev_challenge = self.calculate_expected_value_challenge(player_count, bid)

        best_ev_bid = float("-inf")
        best_bid = None

        # Try all legal raises
        for next_bid in get_valid_perudo_bids(bid, player_count * 5):
            ev = self.calculate_expected_value_bid(player_count, next_bid)
            if ev > best_ev_bid:
                best_ev_bid = ev
                best_bid = next_bid

        # Compare the best raise EV with challenge EV
        if ev_challenge >= best_ev_bid:
            return None
        else:
            return best_bid


# TODO: Update world initialization so its faster
