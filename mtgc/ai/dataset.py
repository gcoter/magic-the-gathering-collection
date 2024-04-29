from typing import Dict

import torch
import numpy as np
import pandas as pd

from mtgc.ai.preprocessing import CardPreprocessor


class DraftDataset(torch.utils.data.Dataset):
    def __init__(self, draft_data_df: pd.DataFrame, cards_data_dict: Dict, card_preprocessor: CardPreprocessor):
        self.draft_data_df = draft_data_df
        self.cards_data_dict = cards_data_dict
        self.card_preprocessor = card_preprocessor

    def __len__(self):
        return len(self.draft_data_df)

    def __getitem__(self, idx):
        row_dict = self.draft_data_df.iloc[idx].to_dict()
        picked_card = row_dict["pick"]
        pool_cards = {
            column.replace("pool_", "").replace("/", " - "): value
            for column, value in row_dict.items()
            if column.startswith("pool_") and value > 0 and column.replace("pool_", "").replace("/", " - ") in self.cards_data_dict
        }
        pack_cards = {
            column.replace("pack_card_", "").replace("/", " - "): value
            for column, value in row_dict.items()
            if column.startswith("pack_card_") and value > 0 and column.replace("pack_card_", "").replace("/", " - ") in self.cards_data_dict
        }

        x = []
        for card_name in pool_cards:
            card_json_dict = self.cards_data_dict[card_name]
            card_vector = self.card_preprocessor.preprocess(card_json_dict)
            card_vector = np.append(card_vector, 0.0)  # To indicate it's part of pool
            card_count = pool_cards[card_name]
            for _ in range(card_count):
                x.append(card_vector)
        for card_name in pack_cards:
            card_json_dict = self.cards_data_dict[card_name]
            card_vector = self.card_preprocessor.preprocess(card_json_dict)
            card_vector = np.append(card_vector, 1.0)  # To indicate it's part of pack
            card_count = pack_cards[card_name]
            for _ in range(card_count):
                x.append(card_vector)

        x = np.array(x)

        y = np.zeros(len(x))
        assert picked_card in pack_cards
        label_index = len(pool_cards) + list(pack_cards.keys()).index(picked_card)
        y[label_index] = 1.0

        return torch.from_numpy(x).float(), torch.from_numpy(y).float()
