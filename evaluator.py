from pyedhrec import EDHRec
import json
import deck
import sys
#https://scryfall.com/docs/api/cards#card-face-objects
edhrec = EDHRec()

oracle_dict = {}

def normalize_name(name):
    return name.strip().lower()

def safe_add(name, card):
    key = normalize_name(name)

    # hopefully this fixes something. skips irrelevant or broken cards
    def is_usable(c):
        return ("cmc" in c and isinstance(c["cmc"], (int, float)) and"oracle_text" in c and isinstance(c["oracle_text"], str) and c.get("layout") not in {"art_series", "token", "emblem"} and not c.get("digital", False))
    # try to replace bad entries with good. doesn't work.
    current = oracle_dict.get(key)
    new_is_good = is_usable(card)
    current_is_good = is_usable(current) if current else False

    if not current or (not current_is_good and new_is_good):
        oracle_dict[key] = card
    elif normalize_name(card.get("name", "")) == key and new_is_good:
        oracle_dict[key] = card


# or whatever your orcale card file is called
#https://scryfall.com/docs/api/bulk-data
with open("oracle-cards-20250718090309.json", "r", encoding="utf-8") as file:
    oracle_cards = json.load(file)

    for card in oracle_cards:
        # skip irrelevant stuff
        if card.get("layout") in {"token", "emblem", "art_series"}:
            continue
        if card.get("digital", False):
            continue
        if card.get("lang") != "en":
            continue
    
        # actually add
        safe_add(card["name"], card)
    
        if "printed_name" in card:
            safe_add(card["printed_name"], card)
        # add each face separately
        if "card_faces" in card:
            for face in card["card_faces"]:
                if "name" in face:
                    safe_add(face["name"], card)



    with open(sys.argv[1], "r", encoding="utf-8") as deck1f:
        deck1 = deck.Deck(''.join([line for line in deck1f]), oracle_dict)
    with open(sys.argv[2], "r", encoding="utf-8") as deck2f:
        deck2 = deck.Deck(''.join([line for line in deck2f]), oracle_dict)
    with open(sys.argv[3], "r", encoding="utf-8") as deck3f:
        deck3 = deck.Deck(''.join([line for line in deck3f]), oracle_dict)
    with open(sys.argv[4], "r", encoding="utf-8") as deck4f:
        deck4 = deck.Deck(''.join([line for line in deck4f]), oracle_dict)


    

    DECK_COLORS = ["cyan", "green", "yellow", "magenta", "blue", "red"]
    #https://rich.readthedocs.io/en/stable/markup.html#console-markup
    from rich.console import Console
    from rich.table import Table
    from rich.text import Text
    
    def average_cmc(curve):
        total_cards = sum(curve.values())
        total_cmc = sum(cmc * count for cmc, count in curve.items() if isinstance(cmc, int))
        return total_cmc / total_cards if total_cards else 0
    
    # U+2588 : FULL BLOCK {solid}
    def make_horizontal_bar(value, max_value, width=20, char="█", color="cyan"):
        if max_value <= 0 or value <= 0:
            return Text("", style=color)
        filled = int((value / max_value) * width)
        return Text(char * filled, style=color)
    
    def curve_comparison_print(decks_with_names):
        console = Console()
        table = Table(title="Mana Curve Comparison")
    
        table.add_column("CMC", justify="right")
        for name, _ in decks_with_names:
            table.add_column(f"{name} Count", justify="right")
            table.add_column(f"{name} Graph", justify="left")
    
        all_cmcs = set()
        for _, curve in decks_with_names:
            all_cmcs.update(cmc for cmc in curve if isinstance(cmc, int))
        max_cmc = max(all_cmcs, default=0)
    
        max_count = max((max((curve.get(cmc, 0) for cmc in all_cmcs), default=0) for _, curve in decks_with_names),default=1)
        #build bar by color, fewest to greatest
        for cmc in range(max_cmc + 1):
            row = [str(cmc)]
            for index, (_, curve) in enumerate(decks_with_names):
                count = curve.get(cmc, 0)
                color = DECK_COLORS[index % len(DECK_COLORS)]
                bar = make_horizontal_bar(count, max_count, width=12, color=color)
                row.append(str(count))
                row.append(bar)
            table.add_row(*row)
        
        console.print(table)
        # print avg cmc at tge bottom
        avg_lines = []
        for (name, curve), color in zip(decks_with_names, DECK_COLORS):
            avg = average_cmc(curve)
            avg_lines.append(f"[{color}]{name} Avg CMC:[/] {avg:.2f}")

        console.print("\n" + "   ".join(avg_lines))
    
    

    curve_comparison_print([(deck1.get_commander_name(), deck1.curve),(deck2.get_commander_name(), deck2.curve),(deck3.get_commander_name(), deck3.curve),(deck4.get_commander_name(), deck4.curve)])

    # see where each deck fits compared to the others. 
    def print_superimposed_curves(decks_with_names):
        console = Console()
        table = Table(title="Superimposed Mana Curve Comparison")
    
        table.add_column("CMC", justify="right")
        table.add_column("Curve", justify="left")
    
        all_cmcs = set()
        for _, curve in decks_with_names:
            all_cmcs.update(cmc for cmc in curve if isinstance(cmc, int))
        max_cmc = max(all_cmcs, default=0)
    
        for cmc in range(max_cmc + 1):
            deck_counts = []
            for idx, (_, curve) in enumerate(decks_with_names):
                count = curve.get(cmc, 0)
                deck_counts.append((count, idx))
    
            # sort by count ascending
            deck_counts.sort()
    
            # max val for each cmc = length of that bar
            max_count = deck_counts[-1][0]
            bar = Text()
    
            last = 0
            for count, index in deck_counts:
                width = count - last
                if width > 0:
                    bar.append("█" * width, style=DECK_COLORS[index % len(DECK_COLORS)])
                    last = count
    
            table.add_row(str(cmc), bar)
    
        console.print(table)
        avg_lines = []
        for (name, curve), color in zip(decks_with_names, DECK_COLORS):
            avg = average_cmc(curve)
            avg_lines.append(f"[{color}]{name} Avg CMC:[/] {avg:.2f}")

        console.print("\n" + "   ".join(avg_lines))
    print_superimposed_curves([(deck1.get_commander_name(), deck1.curve),(deck2.get_commander_name(), deck2.curve),(deck3.get_commander_name(), deck3.curve),(deck4.get_commander_name(), deck4.curve)])

    
    #def red_flags(decks_with_names):
    STATUS_COLORS = {"good": "green", "neutral": "white", "bad": "red", "caution": "yellow",}

    def feature_summary_table(deck_feature_data):
        console = Console()
        table = Table(title="Notable Individual Features")
    
        for index, (deck_name, _) in enumerate(deck_feature_data):
            color = DECK_COLORS[index % len(DECK_COLORS)]
            table.add_column(f"[{color}]{deck_name}[/]", justify="left")
    
        # set how wide our boxes need to be
        max_features = max(len(features) for _, features in deck_feature_data)
    
        for i in range(max_features):
            row = []
            for _, features in deck_feature_data:
                if i < len(features):
                    text, status = features[i]
                    color = STATUS_COLORS.get(status, "white")
                    row.append(Text(text, style=color))
                else:
                    row.append("") 
            table.add_row(*row)
    
        console.print(table)
    
    
    def red_flags(decks):
        result = []
        all_avg_cmcs = []
        all_gamechangers = []
        all_ramp = []
        all_removal = []
    
        for deck in decks:
            flags = []
            name = deck.get_commander_name()
    
            # individual deck considerations
            # removal
            removal_count = (deck.interaction_summary.get("spot_removal", 0) + deck.interaction_summary.get("mass_removal", 0) * 3)
            all_removal.append((name, removal_count))
            if removal_count < 5:
                flags.append(("Low maindeck removal", "bad"))
            elif removal_count < 10:
                flags.append(("Solid maindeck removal", "neutral"))
            else:
                flags.append(("Good maindeck removal", "good"))
    
            # avg cmc
            avg_cmc = sum(cmc * count for cmc, count in deck.curve.items() if isinstance(cmc, int)) / sum(deck.curve.values())
            all_avg_cmcs.append((name, avg_cmc))
            if avg_cmc > 4:
                flags.append(("High average CMC", "neutral"))
            elif avg_cmc > 3:
                flags.append(("Moderate average CMC", "neutral"))
            else:
                flags.append(("Low average CMC", "neutral"))
    
            # ramp
            ramp_count = deck.ramp
            all_ramp.append((name, ramp_count))
            if ramp_count < 4:
                flags.append(("Low ramp", "neutral"))
            elif ramp_count < 8:
                flags.append(("Solid ramp", "neutral"))
            else:
                flags.append(("Strong ramp", "neutral"))
    
            # gamechangers
            gamechangers = deck.gamechangers if hasattr(deck, "gamechangers") else 0
            all_gamechangers.append((name, gamechangers))
            if gamechangers >= 5:
                flags.append(("Has many gamechangers", "bad"))
    
            result.append((name, flags))
    
        # match-level considerations
        match_flags = []
    
        # compare average cmc range
        cmcs_only = [cmc for _, cmc in all_avg_cmcs]
        if max(cmcs_only) - min(cmcs_only) > 1:
            match_flags.append(("Wide disparity in average CMCs, expect someone to steamroll or get steamrolled", "bad"))
    
        # if one deck has > 4 gamechangers and others dont
        outliers = [name for name, count in all_gamechangers if count > 4]
        if len(outliers) == 1:
            match_flags.append((f"{outliers[0]} has many more gamechangers", "bad"))
    
        # big ramp disparity
        ramp_counts = [r for _, r in all_ramp]
        if max(ramp_counts) - min(ramp_counts) > 6:
            match_flags.append(("Significant ramp imbalance across decks", "neutral"))
            
        # tons or little overall removal
        total_removal = 0
        for deck in decks:
            spot = deck.interaction_summary.get("spot_removal", 0)
            mass = deck.interaction_summary.get("mass_removal", 0)
            total_removal += spot + mass * 3
    
        if total_removal < 10:
            match_flags.append(("Very low total removal. Expect snowballing and short games.", "caution"))
        elif total_removal < 25:
            match_flags.append(("Solid table-wide removal.", "good"))
        else:
            match_flags.append(("Loads of overall removal. Games may take a while", "bad"))
            
        # add match-level flags to the result
        result.append(("Match", match_flags))
        return result
    

    feature_summary_table(red_flags([deck1, deck2, deck3, deck4]))


    # you arent gonna find any combos. the list is pretty sparse
    for deck in [deck1, deck2, deck3, deck4]:
        label = deck.get_commander_name()
        combos = deck.detect_combos()
        print(f"{label} Combos Found:")
        if combos:
            for c1, c2 in combos:
                print(f"  {c1} + {c2}")
        else:
            print("  No known combos found.")


