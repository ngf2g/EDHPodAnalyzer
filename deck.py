import re
from collections import defaultdict
# this absolutely does not cover everything.
INTERACTION_PATTERNS = {
            "spot_removal": r"destroy target|exile target|deal \d+ damage to target|return target|destroys target|exiles target|deals \d+ damage to target|returns target",
            "mass_removal": r"destroy all|exile all|each player sacrifices|return each|return all|destroys all|exiles all|returns each|returns all",
            "stack_interaction": r"counter target spell|end the turn",
        }
def normalize_name(name):
    return name.strip().lower()

class Deck:
    def __init__(self, cards, orcale_dict):
        
        sections = {"mainboard": [], "commander": [], "sideboard": []}
        self.sections = sections
        self.oracle_dict = orcale_dict
        lines = cards.splitlines()
        
        # may or may not be a sideboard
        if any("sideboard" in line.lower() for line in lines):
            sb_index = next(i for i, line in enumerate(lines) if "sideboard" in line.lower())
    
            main_lines = lines[:sb_index]
            after_sb_lines = lines[sb_index + 1:]
    
            # only thing separating sections in the file is a space
            sideboard_lines = []
            commander_line = None
            for i, line in enumerate(after_sb_lines):
                if line.strip() == "":
                    # first blank line separates sideboard from commander
                    sideboard_lines = after_sb_lines[:i]
                    if i + 1 < len(after_sb_lines):
                        commander_line = after_sb_lines[i + 1].strip()
                    break
            else:
                # no blank line found, entire remainder is sideboard
                sideboard_lines = [line.strip() for line in after_sb_lines if line.strip()]
    
            # mainboard
            for line in main_lines:
                if not line.strip(): continue
                count, *name_parts = line.strip().split()
                card_name = " ".join(name_parts)
                sections["mainboard"].append((int(count), card_name))
    
            # sideboard. we don't actually care what's in it though, its just here for completion's sake
            for line in sideboard_lines:
                if not line.strip(): continue
                count, *name_parts = line.strip().split()
                card_name = " ".join(name_parts)
                sections["sideboard"].append((int(count), card_name))
    
            # commander
            if commander_line:
                count, *name_parts = commander_line.split()
                card_name = " ".join(name_parts)
                sections["commander"].append((int(count), card_name))
    
        else:
            # no sideboard so assume last line is commander
            clean_lines = [line.strip() for line in lines if line.strip()]
            for line in clean_lines[:-1]:
                count, *name_parts = line.split()
                card_name = " ".join(name_parts)
                sections["mainboard"].append((int(count), card_name))
    
            count, *name_parts = clean_lines[-1].split()
            card_name = " ".join(name_parts)
            sections["commander"].append((int(count), card_name))

        # count interaction
        self.interaction_summary = defaultdict(int)
        for count, name in self.sections["mainboard"]:
            key = name.strip().lower()
            card = self.oracle_dict.get(normalize_name(name))
            if not card:
                continue
            tags = self.detect_interaction(card)
            for tag in tags:
                self.interaction_summary[tag] += count
        self.interaction_summary = dict(self.interaction_summary)
        print(f"INTERACTION FOR {sections["commander"]} DECK: {self.interaction_summary}")

        # calculate mana curve
        self.curve = self.mana_curve(self.oracle_dict)
        print(f"CURVE FOR {sections["commander"]} DECK: {self.curve}")
        
        #count reserved list cards.
        self.reserved_list = 0
        for count, name in self.sections["mainboard"]:
            card = self.oracle_dict.get(normalize_name(name))
            if not card:
                #print(f"Warning: {name} (lookup key: {normalize_name(name)}) not found in oracle data.")
                continue
            if card["reserved"]:
                self.reserved_list += count
        print(f"Reservec cards: {self.reserved_list}")
                
        # count game changer cards.
        self.gamechangers = 0
        for count, name in self.sections["mainboard"]:
            key = name.strip().lower()
            card = self.oracle_dict.get(normalize_name(name))
            if not card:
                continue
            if card["game_changer"] == True:
                self.gamechangers+=1
        print(f"GAME CHANGERS: {self.gamechangers}")

        #count creatures/ noncreatures
        self.creatures = 0
        self.noncreatures = 0
        for count, name in self.sections["mainboard"]:
            card = self.oracle_dict.get(normalize_name(name))
            if not card:
                #print(f"Warning: {name} (lookup key: {normalize_name(name)}) not found in oracle data.")
                continue
            if "creature" in card["type_line"].lower():
                #print(f"Counting {count}x {name} as land")
                self.creatures += count
            elif not "creature" in card["type_line"].lower() and not "land" in card["type_line"].lower():
                self.noncreatures += count
        print(f"Creatures: {self.creatures}, Noncreatures: {self.noncreatures}")
        
        #count lands
        self.lands = 0
        for count, name in self.sections["mainboard"]:
            card = self.oracle_dict.get(normalize_name(name))
            if not card:
                #print(f"Warning: {name} (lookup key: {normalize_name(name)}) not found in oracle data.")
                continue
            if "land" in card["type_line"].lower():
                #print(f"Counting {count}x {name} as land")
                self.lands += count
        print(f"LANDS: {self.lands}")

        #calculate ramp
        self.ramp = 0
        for count, name in self.sections["mainboard"]:
            card = self.oracle_dict.get(normalize_name(name))
            if not card:
                #print(f"Warning: {name} (lookup key: {normalize_name(name)}) not found in oracle data.")
                continue
            if "land" not in card["type_line"].lower() and card.get("produced_mana"):
                #print(f"Counting {count}x {name} as land")
                self.ramp += count
        print(f"Ramp: {self.ramp}")
        
        # update curve by subtracting lands from 0 costs
        self.curve = self.mana_curve(self.oracle_dict)
        if 0 in self.curve:
            self.curve[0] = max(0, self.curve[0] - self.lands)
            
        # get total deck price, because you might make people mad if youre rich and theyre broke.
        self.total_price_usd = 0.0
        for section in ["mainboard", "commander", "sideboard"]:
            for count, name in self.sections[section]:
                card = self.oracle_dict.get(normalize_name(name))
                if card:
                    price = self.get_card_price(card)
                    self.total_price_usd += count * price
        print(f"Deck price: ${self.total_price_usd:.2f}")

    def get_card_price(self, card):
        prices = card.get("prices", {})
        for key in ["usd", "usd_foil", "usd_etched"]:
            price_str = prices.get(key)
            if price_str:
                try:
                    return float(price_str)
                except ValueError:
                    pass
        return 0.0  # just do 0 if no valid price

        
    def mana_curve(self, card_lookup):
        cmc_counts = defaultdict(int)
        for count, name in self.sections["mainboard"]:
            key = name.strip().lower()
            if key not in card_lookup:
                #print(f"Warning: {name} (lookup key: {normalize_name(name)}) not found in oracle data.")
                continue
            cmc = int(card_lookup[key]["cmc"])
            cmc_counts[cmc] += count
        return dict(cmc_counts)

    def detect_interaction(self, card):
        
        if "oracle_text" not in card:
            return []
    
        text = card["oracle_text"].lower()
        matches = []
    
        for label, pattern in INTERACTION_PATTERNS.items():
            if re.search(pattern, text):
                matches.append(label)
    
        return matches

    # this doesn't work. dunno why. i gave up.
    def detect_combos(self):
        combos = []
        deck_card_names = {normalize_name(name) for section in self.sections.values() for _, name in section}
    
        for _, name in self.sections["mainboard"]:
            card_data = self.oracle_dict.get(normalize_name(name))
            if not card_data:
                continue
    
            all_parts = card_data.get("all_parts", [])
            for part in all_parts:
                if part.get("component") != "combo_piece":
                    continue
                part_name = normalize_name(part.get("name", ""))
                if part_name in deck_card_names and part_name != normalize_name(name):
                    # no dupes
                    combo = tuple(sorted((normalize_name(name), part_name)))
                    if combo not in combos:
                        combos.append(combo)
    
        return combos
    
    def get_commander_name(self):
        if self.sections["commander"]:
            _, name = self.sections["commander"][0]
            return name
        return "Unknown"
