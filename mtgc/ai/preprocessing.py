import re

import numpy as np


def filter_draft_data(draft_data_df, cards_data_dict):
    print(f"Filter draft data (current shape: {draft_data_df.shape})")

    # Make sure each pick is part of the the known cards
    # FIXME: Handle cases like 'Kellan, Inquisitive Prodigy // Tail the Suspect'
    draft_data_df = draft_data_df[draft_data_df["pick"].isin(cards_data_dict)]

    # Filter good players
    draft_data_df = draft_data_df[draft_data_df["user_game_win_rate_bucket"] >= 0.62]
    draft_data_df = draft_data_df[draft_data_df["user_n_games_bucket"] >= 100]

    # Keep only situations with at least 2 pack cards
    pack_columns = [column for column in draft_data_df.columns if "pack_card_" in column]
    draft_data_df = draft_data_df[draft_data_df[pack_columns].sum(axis=1) >= 2]

    # Remove first pick situations
    pool_columns = [column for column in draft_data_df.columns if "pool_" in column]
    draft_data_df = draft_data_df[draft_data_df[pool_columns].sum(axis=1) >= 1]

    print(f"Filtering done (new shape: {draft_data_df.shape})")

    return draft_data_df.reset_index(drop=True)


class CardPreprocessor:
    def __init__(self, card_type_vocabulary, keyword_vocabulary):
        self.card_type_vocabulary = card_type_vocabulary
        self.keyword_vocabulary = keyword_vocabulary

    def preprocess(self, card_json_dict):
        vectors = []
        vectors.append(self.__compute_card_type_vector(card_json_dict))
        vectors.append(self.__compute_mana_cost_vector(card_json_dict))
        vectors.append(self.__compute_power_toughness_vector(card_json_dict))
        vectors.append(self.__compute_keyword_vector(card_json_dict))
        vectors.append(self.__compute_17lands_vector(card_json_dict))
        return np.concatenate(vectors, axis=0)

    def get_feature_names(self):
        feature_names = []
        for card_type in self.card_type_vocabulary:
            feature_names.append(f"is_{card_type.lower()}")
        feature_names.extend([
            "mana_cost_W",
            "mana_cost_U",
            "mana_cost_B",
            "mana_cost_R",
            "mana_cost_G",
            "mana_cost_C",
        ])
        feature_names.extend([
            "power",
            "toughness"
        ])
        for keyword in self.keyword_vocabulary:
            feature_names.append(f"has_{keyword.lower()}")
        feature_names.extend([
            "17lands_GIH_WR"
        ])
        return feature_names

    def __compute_card_type_vector(self, card_json_dict):
        type_line = card_json_dict["scryfall"]["type_line"]
        card_type = type_line.split(" — ")[0]
        vector = []
        for card_type_vocabulary_item in self.card_type_vocabulary:
            if card_type_vocabulary_item in card_type:
                vector.append(1.0)
            else:
                vector.append(0.0)
        return np.array(vector)

    def __compute_mana_cost_vector(self, card_json_dict):
        mana_cost = card_json_dict["scryfall"]["mana_cost"]

        colorless = re.findall("\d", mana_cost)
        if len(colorless) > 0:
            # FIXME: Handle cases like 'Bonecrusher Giant' with two costs
            colorless = int(colorless[0])
        elif len(colorless) == 0:
            colorless = 0
        else:
            raise ValueError()

        return np.array([
            mana_cost.count("{W}"),
            mana_cost.count("{U}"),
            mana_cost.count("{B}"),
            mana_cost.count("{R}"),
            mana_cost.count("{G}"),
            colorless
        ]) / 10

    def __compute_power_toughness_vector(self, card_json_dict):
        power = -1
        toughness = -1

        if "power" in card_json_dict["scryfall"]:
            if isinstance(card_json_dict["scryfall"]["power"], int):
                # FIXME: Handle cases where power is not int
                power = card_json_dict["scryfall"]["power"]
        if "toughness" in card_json_dict["scryfall"]:
            if isinstance(card_json_dict["scryfall"]["toughness"], int):
                # FIXME: Handle cases where toughness is not int
                toughness = card_json_dict["scryfall"]["toughness"]
        return np.array([
            power,
            toughness
        ]) / 10

    def __compute_keyword_vector(self, card_json_dict):
        keywords = card_json_dict["scryfall"]["keywords"]
        if len(keywords) == 0:
            return np.zeros(len(self.keyword_vocabulary))
        vector = []
        for keyword in self.keyword_vocabulary:
            if keyword in keywords:
                vector.append(1.0)
            else:
                vector.append(0.0)
        return np.array(vector)

    def __compute_17lands_vector(self, card_json_dict):
        games_in_hand_win_rate = -1.0
        if "17lands" in card_json_dict:
            if "GIH WR" in card_json_dict["17lands"]:
                if card_json_dict["17lands"]["GIH WR"] is not None:
                    games_in_hand_win_rate = card_json_dict["17lands"]["GIH WR"] / 100
        return np.array([
            games_in_hand_win_rate
        ])
