import re


class CardPairFeatureExtractor:
    def extract(self, card_json_dict_1, card_json_dict_2):
        mana_cost_by_color_1 = self.__extract_mana_cost_by_color(card_json_dict_1["scryfall"]["mana_cost"] if "mana_cost" in card_json_dict_1["scryfall"] else "", suffix="1")
        mana_cost_by_color_2 = self.__extract_mana_cost_by_color(card_json_dict_2["scryfall"]["mana_cost"] if "mana_cost" in card_json_dict_2["scryfall"] else "", suffix="2")
        n_common_types = len(set(card_json_dict_1["scryfall"]["type_line"].split(" \u2014 ")).intersection(set(card_json_dict_2["scryfall"]["type_line"].split(" \u2014 "))))
        n_common_keywords = len(set(card_json_dict_1["scryfall"]["keywords"]).intersection(set(card_json_dict_2["scryfall"]["keywords"])))

        return {
            **mana_cost_by_color_1,
            **mana_cost_by_color_2,
            "n_common_types": n_common_types,
            "n_common_keywords": n_common_keywords
        }

    def __extract_mana_cost_by_color(self, mana_cost_string, suffix):
        colorless = re.findall("\d", mana_cost_string)
        if len(colorless) > 0:
            # FIXME: Handle cases like 'Bonecrusher Giant' with two costs
            colorless = int(colorless[0])
        elif len(colorless) == 0:
            colorless = 0
        else:
            raise ValueError()
        return {
            f"mana_cost_C_{suffix}": colorless,
            f"mana_cost_U_{suffix}": mana_cost_string.count("{U}"),
            f"mana_cost_G_{suffix}": mana_cost_string.count("{G}"),
            f"mana_cost_B_{suffix}": mana_cost_string.count("{B}"),
            f"mana_cost_W_{suffix}": mana_cost_string.count("{W}"),
            f"mana_cost_R_{suffix}": mana_cost_string.count("{R}"),
        }
