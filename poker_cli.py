#!/usr/bin/env python3
import argparse

def rule_of_2_and_4(outs: int, cards_left_to_see: int) -> float:
    if cards_left_to_see == 2:
        return min(1.0, outs * 0.04)  # 4% per out
    elif cards_left_to_see == 1:
        return min(1.0, outs * 0.02)  # 2% per out
    else:
        return min(1.0, outs * 0.04)


def exact_probability_by_outs(outs: int, cards_left_to_see: int, visible_cards: int = 5) -> float:
    deck_size = 52 - visible_cards  # naive approach
    
    p_no_out = 1.0
    for i in range(cards_left_to_see):
        p_no_out *= (deck_size - outs - i) / (deck_size - i)

    return 1.0 - p_no_out


def pot_odds(pot_size: float, call_amount: float) -> float:
    return (pot_size + call_amount) / call_amount


def main():
    parser = argparse.ArgumentParser(
        description="Poker CLI: Calculate outs-based hand probabilities and compare to pot odds."
    )

    parser.add_argument(
        "--outs",
        type=int,
        required=True,
        help="Number of outs to hit your draw."
    )
    parser.add_argument(
        "--cards_left_to_see",
        type=int,
        default=2,
        choices=[1, 2],
        help="Number of cards left to be dealt (1 for turn, 2 for turn+river)."
    )
    parser.add_argument(
        "--pot_size",
        type=float,
        default=0.0,
        help="Current total pot size before calling."
    )
    parser.add_argument(
        "--call_amount",
        type=float,
        default=0.0,
        help="Amount you need to call to stay in the hand."
    )
    parser.add_argument(
        "--visible_cards",
        type=int,
        default=5,
        help="Number of already-seen cards (default 5 for pre-turn; 2 hole + 3 flop)."
    )
    parser.add_argument(
        "--method",
        choices=["rule_of_2_4", "exact"],
        default="rule_of_2_4",
        help="Which method to use for calculating the improvement probability."
    )

    args = parser.parse_args()

    # Calculate probability
    if args.method == "rule_of_2_4":
        win_probability = rule_of_2_and_4(args.outs, args.cards_left_to_see)
    else:
        # Use the more 'exact' approach
        win_probability = exact_probability_by_outs(
            args.outs, args.cards_left_to_see, args.visible_cards
        )

    odds_against = 0
    if win_probability < 1.0:
        odds_against = (1.0 - win_probability) / win_probability
    else:
        odds_against = 0.0 

    final_pot_odds = 0.0
    if args.call_amount > 0:
        final_pot_odds = pot_odds(args.pot_size, args.call_amount)
    else:
        final_pot_odds = 0.0

    # Display results
    print("===== Poker CLI Results =====")
    print(f"Outs: {args.outs}")
    print(f"Cards left to see: {args.cards_left_to_see}")
    print(f"Method: {args.method}")
    print(f"Win Probability: {win_probability:.2%}")
    print(f"Odds Against (Your hand): {odds_against:.2f}:1")

    if args.call_amount > 0:
        print(f"Pot Size: {args.pot_size}")
        print(f"Call Amount: {args.call_amount}")
        print(f"Pot Odds: {final_pot_odds:.2f}:1")

        if final_pot_odds >= odds_against:
            print("=> Pot odds are favorable compared to your odds of hitting (profitable call).")
        else:
            print("=> Pot odds are NOT favorable compared to your odds of hitting (fold might be better).")
    else:
        print("No call amount specified, skipping pot odds comparison.")


if __name__ == "__main__":
    main()