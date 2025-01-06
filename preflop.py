#!/usr/bin/env python3

import argparse
import re


PREMIUM = {
    "AA", "KK", "QQ", "JJ", "TT",
    "AKs", "AQs", "AJs", "KQs",
    "AKo", 
}

STRONG = {
    "AJo", "AQo", "KQo",
    "99", "88", "77",
    "ATs", "KJs", "QJs", "JTs",
    "KTs", "QTs", "J9s", 
}

SPECULATIVE = {
    "66", "55", "44", "33", "22",
    "A9s", "A8s", "A7s", "A5s", "A4s", "A3s", "A2s",
    "KJo", "QJo", "T9s", "98s", "87s", "76s",
    "T8s", "97s", "86s", "65s", 
}


POSITION_GROUPS = {
    "ep": {
        "raise": PREMIUM.union(STRONG),
        "call": SPECULATIVE,
    },
    "mp": {
        "raise": PREMIUM.union(STRONG),
        "call": SPECULATIVE,
    },
    "lp": {
        "raise": PREMIUM.union(STRONG).union(SPECULATIVE),
        "call": set(), 
    },
}

def normalize_hand(hole_cards: str) -> str:
    """
    Convert a string like 'AhKc' or 'AsKd' into a simplified pattern like:
    - 'AKs' if both are suited
    - 'AKo' if offsuit
    - 'AA' if same rank
    - 'JJ', etc.

    We only need ranks (A, K, Q, J, T, 9,...2) and an 's' or 'o'.
    """
    # 1. Extract cards (assuming the user might provide something like "AhKc"):
    #    We expect two cards, each with rank + suit.
    #    E.g. "Ah" = (A, h), "Kc" = (K, c)
    
    pattern = re.findall(r'([AKQJT2-9][hcds])', hole_cards, re.IGNORECASE)
    if len(pattern) < 2:
        # If user typed "A K" or something, try splitting on whitespace
        pattern = hole_cards.split()

    if len(pattern) != 2:
        # Just in case
        return None

    card1, card2 = pattern[0], pattern[1]

    rank1, suit1 = card1[0].upper(), card1[1].lower()
    rank2, suit2 = card2[0].upper(), card2[1].lower()

    rank_order = {'A': 14, 'K': 13, 'Q': 12, 'J': 11, 'T': 10,
                  '9': 9, '8': 8, '7': 7, '6': 6, '5': 5, '4': 4, '3': 3, '2': 2}

    if rank_order[rank2] > rank_order[rank1]:
        rank1, rank2 = rank2, rank1
        suit1, suit2 = suit2, suit1

    if suit1 == suit2:
        if rank1 == rank2:
            return rank1 + rank2  # e.g. "AA", "KK"
        else:
            return f"{rank1}{rank2}s"
    else:
        if rank1 == rank2:
            return rank1 + rank2  # e.g. "AA"
        else:
            return f"{rank1}{rank2}o"


def get_preflop_suggestion(normalized_hand: str, position: str) -> str:
    """
    Given a normalized hand like 'AKs' and a position ('ep', 'mp', 'lp'),
    return a suggestion: 'raise', 'call', or 'fold'.
    """
    if normalized_hand in POSITION_GROUPS[position]["raise"]:
        return "raise"
    
    if normalized_hand in POSITION_GROUPS[position]["call"]:
        return "call"
    
    return "fold"


def main():
    parser = argparse.ArgumentParser(
        description="Simplified Pre-Flop Decision CLI for Texas Hold'em"
    )
    parser.add_argument(
        "--cards",
        type=str,
        required=True,
        help="Your two hole cards (e.g. 'Ah Kc' or 'Ks Kh')."
    )
    parser.add_argument(
        "--position",
        type=str,
        default="ep",
        choices=["ep", "mp", "lp"],
        help="Your table position: ep (early), mp (middle), lp (late)."
    )

    args = parser.parse_args()

    normalized = normalize_hand(args.cards)
    if not normalized:
        print("Error: Could not parse your hole cards. Make sure to provide them like 'AhKc' or 'Ah Kc'.")
        return

    suggestion = get_preflop_suggestion(normalized, args.position)

    print("===== Pre-Flop Decision Tool =====")
    print(f"Hole cards: {args.cards} -> Normalized: {normalized}")
    print(f"Position: {args.position}")
    print(f"Suggested Action: {suggestion.upper()}")


if __name__ == "__main__":
    main()