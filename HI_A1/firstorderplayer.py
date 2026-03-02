from __future__ import annotations

import itertools
import math

from perudo import PerudoBid, PerudoPlayer, get_valid_perudo_bids
from zeroorderplayer import ZeroOrderPlayer


class FirstOrderPlayer(PerudoPlayer):
    """
    Implementation of a first-order theory of mind agent.
    Author: Jesse Kerkhof (j.j.kerkhof@student.rug.nl)
    """

    def _world_to_dice(self, k_tuple: tuple[int]) -> tuple[int]:
        """Converts a multinomial dice-count into an explicit tuple of dice faces.

        Args:
            k_tuple (tuple[int]): Tuple representing possible world state, example input (2, 0, 1, 0, 2, 0)

        Returns:
            tuple[int]: Tuple representing real dice in the hand, example output (1, 1, 3, 5, 5)
        """
        dice_list = []
        for face in range(1, 7):
            for _ in range(k_tuple[face - 1]):
                dice_list.append(face)
        return tuple(dice_list)

    def start_game(self, identifier: int, dice: tuple[int]) -> None:
        """Initializes the game for the ToM1-agent.

        Args:
            identifier (int): Integer representing the identity of the agent.
            dice (tuple[int]): Dice of the agent.
        """
        self.my_dice = dice

        self.player_count = 2
        total_opp_dice = (self.player_count - 1) * 5

        # Multinomial prior over opponent dice counts
        self.beliefs = {}
        for k_tuple in itertools.product(range(total_opp_dice + 1), repeat=6):
            if sum(k_tuple) == total_opp_dice:
                numerator = math.factorial(total_opp_dice)
                denominator = math.prod(math.factorial(k) for k in k_tuple)
                prob = (numerator / denominator) * ((1 / 6) ** total_opp_dice)
                self.beliefs[k_tuple] = prob

        self.previous_bid = None

        self.epsilon = 0.05

    def tom0_decision(
        self, dice: tuple[int], bid: PerudoBid | None
    ) -> PerudoBid | None:
        """Function that simulates the ZeroOrderPlayer() decision making for the use of the FirstOrderPlayer().

        Args:
            dice (tuple[int]): The dice that ZeroOrderPlayer() is holding
            bid (PerudoBid | None): The incoming bid.

        Returns:
            PerudoBid | None: Either returns the best possible bid or challenges, based on statistical likelihood from assignment 1.
        """

        valid_bids = get_valid_perudo_bids(bid, 5 * self.player_count)

        # Calculate raise probabilities
        best_raise = None
        best_p = 0.0
        for b in valid_bids:
            p = ZeroOrderPlayer().calculate_bid_chance(dice, self.player_count, b)
            if p > best_p:
                best_p = p
                best_raise = b

        # Calculate challenge probability
        p_challenge = ZeroOrderPlayer().calculate_challenge_chance(
            dice, self.player_count, bid
        )

        # Compare
        if p_challenge >= best_p:
            return None
        else:
            return best_raise

    def observe_bid(self, bid: PerudoBid, player: int) -> None:
        """Function that implements the bayesian beliefs updating.

        Args:
            bid (PerudoBid): Incoming bid.
            player (int): Current plyer

        Returns:
            None: Function only updates variables.
        """
        # First incoming bid: no update
        if self.previous_bid is None:
            self.previous_bid = bid
            return

        new_beliefs = {}
        beta = 0.0

        valid_bids = get_valid_perudo_bids(self.previous_bid, 5 * self.player_count)
        n = len(valid_bids) + 1  # +1 for challenge

        for k_tuple, prior in self.beliefs.items():
            hypothetical_dice = self._world_to_dice(k_tuple)

            # What would a TOM0 agent do with these dice?
            tom0_action = self.tom0_decision(hypothetical_dice, self.previous_bid)

            # Bayes
            if tom0_action == bid:
                likelihood = 1 - self.epsilon
            else:
                likelihood = self.epsilon / n

            posterior_unnormalized = likelihood * prior
            new_beliefs[k_tuple] = posterior_unnormalized
            beta += posterior_unnormalized

        # Normalize
        if beta > 0:
            for k in new_beliefs:
                new_beliefs[k] /= beta
        else:
            # Should not happen, but fall back to prior
            pass

        self.beliefs = new_beliefs
        self.previous_bid = bid

    def observe_challenge(self, bid: PerudoBid, player: int, success: bool) -> None:
        pass

    def calculate_expected_value_challenge(self, bid: PerudoBid) -> float:
        """Function that calculates EV_challenge.

        Args:
            bid (PerudoBid): Incoming bid.

        Returns:
            float: The expected value of challenging the bid.
        """
        win_prob = 0.0
        lose_prob = 0.0

        for k_tuple, belief in self.beliefs.items():
            opponent_kf = k_tuple[bid.face_value - 1]
            my_kf = self.my_dice.count(bid.face_value)

            # Win challenge if bid is false in world s
            if opponent_kf + my_kf < bid.count:
                win_prob += belief
            else:
                lose_prob += belief

        return win_prob - lose_prob

    def calculate_expected_value_bid(self, new_bid: PerudoBid) -> float:
        """Function that calculates EV_bid

        Args:
            new_bid (PerudoBid): The candidate raise being evaluated.

        Returns:
            float: The expected value of raising this bid.
        """
        win_prob = 0.0
        lose_prob = 0.0

        for k_tuple, belief in self.beliefs.items():
            hypothetical_dice = self._world_to_dice(k_tuple)
            opponent_kf = k_tuple[new_bid.face_value - 1]
            my_kf = self.my_dice.count(new_bid.face_value)

            # Probability TOM0 challenges our new bid
            p_challenge = ZeroOrderPlayer().calculate_challenge_chance(
                hypothetical_dice, self.player_count, new_bid
            )

            # Bid true in world s leads to TOM0 challenging gives us a win
            if opponent_kf + my_kf >= new_bid.count:
                win_prob += belief * p_challenge
            else:
                lose_prob += belief * p_challenge

        return win_prob - lose_prob

    def take_turn(
        self, dice: tuple[int], player_count: int, bid: PerudoBid | None
    ) -> PerudoBid | None:
        """Function that implements the turn-taking logic for a First Order Theory of Mind Perudo Player.

        Args:
            dice (tuple[int]): Agent's dice
            player_count (int): Amount of players in the game.
            bid (PerudoBid | None): Incoming bid.

        Returns:
            PerudoBid | None: Either raise the bid to (k*, f*) or challenge the incoming bid, based on which has the higher expected value.
        """
        # Case 1 - We make the initial bid
        if bid is None:
            best_ev = float("-inf")
            best_bid = None

            for next_bid in get_valid_perudo_bids(None, 5 * player_count):
                ev = self.calculate_expected_value_bid(next_bid)
                if ev > best_ev:
                    best_ev = ev
                    best_bid = next_bid
            return best_bid

        # Case 2 - Evaluate challenge
        ev_challenge = self.calculate_expected_value_challenge(bid)

        # Case 3 - Evaluate all legal raises
        best_ev_bid = float("-inf")
        best_bid = None

        for next_bid in get_valid_perudo_bids(bid, 5 * player_count):
            ev = self.calculate_expected_value_bid(next_bid)
            if ev > best_ev_bid:
                best_ev_bid = ev
                best_bid = next_bid

        # Final decision
        if ev_challenge >= best_ev_bid:
            return None
        else:
            return best_bid
