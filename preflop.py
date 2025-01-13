#!/usr/bin/env python3

import argparse
import re
import datetime
import sys

RANGES = {
    # Under the Gun (tightest)
    "utg": {
        "raise": {
            "AA", "KK", "QQ", "JJ", "TT", "AKs", "AQs", "AJs", "KQs", "AKo"
        },
        "call": {
            "99", "88", "77", "66", "55", "44", "33", "22"
        },
    },
    # Middle Position
    "mp": {
        "raise": {
            "AA", "KK", "QQ", "JJ", "TT",
            "AKs", "AQs", "AJs", "ATs", "KQs",
            "AKo", "AQo", "AJo", "KQo", 
        },
        "call": {
            "99", "88", "77", "66", "55", "44", "33", "22",
            "KJs", "QJs", "T9s",  # some suited connectors
        },
    },
    # Hijack
    "hj": {
        "raise": {
            "AA", "KK", "QQ", "JJ", "TT", "99",
            "AKs", "AQs", "AJs", "ATs", "KQs", "KJs",
            "AKo", "AQo", "AJo", "KQo", "KJo"
        },
        "call": {
            "88", "77", "66", "55", "44", "33", "22",
            "QJs", "JTs", "T9s", "98s"
        },
    },
    # Cutoff
    "co": {
        "raise": {
            # Wider than HJ
            "AA", "KK", "QQ", "JJ", "TT", "99", "88",
            "AKs", "AQs", "AJs", "ATs", "KQs", "KJs", "QJs", 
            "AKo", "AQo", "AJo", "KQo", "KJo", "QJo", 
            "JTs", "T9s", "98s", 
        },
        "call": {
            "77", "66", "55", "44", "33", "22",
            "A9s", "KTs", "QTs", "J9s", "87s", "76s"
        },
    },
    # Button
    "btn": {
        "raise": {
            # Very wide
            "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", 
            "AKs", "AQs", "AJs", "ATs", "KQs", "KJs", "QJs", "JTs", 
            "AKo", "AQo", "AJo", "KQo", "KJo", "QJo", 
            "T9s", "98s", "87s", "76s", 
            "A9s", "A8s", "A5s" 
        },
        "call": {
            "66", "55", "44", "33", "22",
            "KTs", "QTs", "J9s", "T8s", "97s", "86s"
        },
    },
    # Small Blind
    "sb": {
        "raise": {
            "AA", "KK", "QQ", "JJ", "TT", "99", "88", 
            "AKs", "AQs", "AJs", "ATs", "KQs", "KJs",
            "AKo", "AQo", "AJo", "KQo",
            "QJs", "JTs", "T9s", "98s" # etc.
        },
        "call": {
            "77", "66", "55", "44", "33", "22", 
            "A9s", "KTs", "QTs", "J9s", "87s", "76s" 
        },
    },
    "bb": {
        "raise": {
            "AA", "KK", "QQ", "JJ", "TT",
            "AKs", "AQs", "AJs", "KQs",
            "AKo", "AQo", "AJo", "KQo",
        },
        "call": {
            "99", "88", "77", "66", "55", "44", "33", "22",
            "ATs", "KJs", "QJs", "JTs", "T9s", "98s", "87s", "76s",
            "A9s", "KTs", "QTs", "J9s", "T8s",
        },
    },
}


def normalize_hand(hole_cards: str) -> str:
    import re
    pattern = re.findall(r'([AKQJT2-9][hcds])', hole_cards, re.IGNORECASE)
    if len(pattern) < 2:
        # fallback: try splitting
        pattern = hole_cards.split()

    if len(pattern) != 2:
        return None

    card1, card2 = pattern[0], pattern[1]
    rank_order = {'A': 14, 'K': 13, 'Q': 12, 'J': 11, 'T': 10,
                  '9': 9, '8': 8, '7': 7, '6': 6, '5': 5, '4': 4, '3': 3, '2': 2}

    # Separate rank and suit
    r1, s1 = card1[0].upper(), card1[1].lower()
    r2, s2 = card2[0].upper(), card2[1].lower()

    # Sort so highest rank is first
    if rank_order[r2] > rank_order[r1]:
        r1, r2 = r2, r1
        s1, s2 = s2, s1

    # If same suit and same rank => e.g. 'AA'
    if r1 == r2:
        return r1 + r2  # 'AA', 'KK', etc.

    # Check suited or offsuit
    if s1 == s2:
        return f"{r1}{r2}s"
    else:
        return f"{r1}{r2}o"


def get_preflop_suggestion(hand: str, position: str, stack_size: float, action_before: str) -> (str, str):
    if position not in RANGES:
        return ("fold", f"Position {position} not recognized in RANGES.")

    pos_ranges = RANGES[position]
    is_in_raise_range = (hand in pos_ranges["raise"])
    is_in_call_range = (hand in pos_ranges["call"])

    # Check stack size
    if stack_size < 20:
        # Simplified "push or fold" range if short-stacked
        if is_in_raise_range:
            return ("all-in", "Short-stacked strategy: Push with premium/strong range.")
        else:
            return ("fold", "Short-stacked strategy: Hand not strong enough to shove.")
    else:
        # If there's prior action
        if action_before == "none":
            # We are first to act (open)
            if is_in_raise_range:
                return ("raise", "Open-raise with a strong or premium hand.")
            elif is_in_call_range:
                return ("call", "You might limp/call with a speculative hand if table conditions allow.")
            else:
                return ("fold", "Not in raise/call range for your position. Fold.")
        elif action_before == "raise":
            # Someone else has raised already
            # Typically we 3-bet or fold, but let's say we call with certain pockets/suited connectors
            if is_in_raise_range:
                return ("3-bet", "Facing a raise: 3-bet with your strong range.")
            elif is_in_call_range:
                return ("call", "Facing a raise: Flat-call with your speculative hand.")
            else:
                return ("fold", "Facing a raise: Hand not strong enough. Fold.")
        elif action_before == "call":
            # There's a caller ahead, but no raise
            if is_in_raise_range:
                return ("raise", "Isolate the limper with a strong hand.")
            elif is_in_call_range:
                return ("call", "Over-limp with a speculative hand.")
            else:
                return ("fold", "Not strong enough to raise or call. Fold.")
        elif action_before == "3bet":
            # There's already a 3-bet, so only top range
            if is_in_raise_range and hand in {"AA", "KK", "QQ", "AKs", "AKo"}:
                return ("4-bet", "Facing a 3-bet: 4-bet only top-tier hands.")
            else:
                return ("fold", "Facing a 3-bet: This hand is not strong enough.")
        else:
            return ("fold", f"Unknown action_before={action_before}; defaulting to fold.")


def get_recommended_raise_size(position: str, stack_size: float) -> float:
    if position in ["utg", "mp", "hj"]:
        return 3.0
    elif position == "co":
        return 2.5
    elif position == "btn":
        return 2.2
    elif position == "sb":
        return 3.0
    elif position == "bb":
        return 3.0
    else:
        return 2.5  # fallback


def log_decision(cards: str, normalized: str, position: str, stack_size: float, action_before: str,
                 suggestion: str, explanation: str, filename="preflop_suggestions.csv"):
    timestamp = datetime.datetime.now().isoformat()
    with open(filename, "a") as f:
        f.write(f"{timestamp},{cards},{normalized},{position},{stack_size},{action_before},{suggestion},{explanation}\n")

def run_interactive():
    print("=== Interactive Pre-Flop Advisor ===")
    cards = input("Enter your hole cards (e.g. 'Ah Kc'): ")
    position = input("Enter your position (utg/mp/hj/co/btn/sb/bb): ").lower()
    stack_size_str = input("Enter your effective stack size in BB (e.g. 40): ")
    action_before = input("Any prior action? (none/raise/call/3bet): ").lower()

    try:
        stack_size = float(stack_size_str)
    except ValueError:
        print("Invalid stack size. Using 100 BB by default.")
        stack_size = 100.0

    normalized = normalize_hand(cards)
    if not normalized:
        print("Error parsing hole cards. Exiting.")
        return

    # Get suggestion
    suggestion, explanation = get_preflop_suggestion(normalized, position, stack_size, action_before)

    # Display recommendation
    print("\n=== Decision ===")
    print(f"Your hand: {cards} -> Normalized: {normalized}")
    print(f"Position: {position.upper()} | Stack: {stack_size}BB | Prior Action: {action_before}")
    print(f"Suggested Action: {suggestion.upper()}")
    if suggestion in ["raise", "3-bet", "4-bet"]:
        r_size = get_recommended_raise_size(position, stack_size)
        print(f"Recommended Raise Size: ~{r_size:.1f}x BB")
    print(f"Reason: {explanation}")

    # Log the decision
    log_decision(cards, normalized, position, stack_size, action_before, suggestion, explanation)


def main():
    parser = argparse.ArgumentParser(
        description="Enhanced Pre-Flop Decision CLI"
    )
    parser.add_argument(
        "--cards",
        type=str,
        help="Your two hole cards, e.g. 'Ah Kc'."
    )
    parser.add_argument(
        "--position",
        type=str,
        choices=["utg", "mp", "hj", "co", "btn", "sb", "bb"],
        help="Table position."
    )
    parser.add_argument(
        "--stack_size",
        type=float,
        default=100.0,
        help="Effective stack size in Big Blinds."
    )
    parser.add_argument(
        "--action_before",
        type=str,
        choices=["none", "raise", "call", "3bet"],
        default="none",
        help="Prior action before you. (none/raise/call/3bet)"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive mode (prompts user for input)."
    )

    args = parser.parse_args()

    # If interactive, just run the interactive flow and ignore the other arguments
    if args.interactive:
        run_interactive()
        sys.exit(0)

    # Otherwise, we use the arguments. All must be present for a straightforward run.
    if not args.cards or not args.position:
        print("Error: --cards and --position are required in non-interactive mode (or use --interactive).")
        sys.exit(1)

    normalized = normalize_hand(args.cards)
    if not normalized:
        print("Error: Could not parse your hole cards.")
        sys.exit(1)

    suggestion, explanation = get_preflop_suggestion(
        normalized,
        args.position,
        args.stack_size,
        args.action_before
    )

    print("=== Enhanced Pre-Flop Advisor ===")
    print(f"Hand: {args.cards} -> Normalized: {normalized}")
    print(f"Position: {args.position.upper()} | Stack: {args.stack_size}BB | Prior Action: {args.action_before}")
    print(f"Suggested Action: {suggestion.upper()}")
    if suggestion in ["raise", "3-bet", "4-bet"]:
        r_size = get_recommended_raise_size(args.position, args.stack_size)
        print(f"Recommended Size: ~{r_size:.1f}x BB")
    print(f"Reason: {explanation}")

    log_decision(args.cards, normalized, args.position, args.stack_size,
                 args.action_before, suggestion, explanation)


if __name__ == "__main__":
    main()