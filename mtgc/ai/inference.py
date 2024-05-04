import torch
import numpy as np
import pandas as pd

from mtgc.ai.model import DraftPicker


class DraftPickerInference:
    def __init__(self, model: DraftPicker, cards_data_dict, card_preprocessor):
        self.device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
        self.model = model.to(self.device).eval()
        self.cards_data_dict = cards_data_dict
        self.card_preprocessor = card_preprocessor

    def run(self, pool_cards, pack_cards, picked_card, explain=False):
        x = self.__cards_to_tensors(pool_cards, pack_cards)
        y_probs = self.__predict_probabilities(x)

        print("\n===== Situation =====\n")
        self.__print_situation(pool_cards, pack_cards)

        print("\n===== Predictions =====\n")
        self.__print_predictions(pool_cards, pack_cards, picked_card, y_probs)

        if explain:
            print("\n===== Explanation =====\n")
            self.__print_gradient_explainability(pool_cards, pack_cards, x, y_probs)

    def __cards_to_tensors(self, pool_cards, pack_cards):
        # FIXME: Copy pasted from dataset
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
        x = torch.from_numpy(x).float()
        x = torch.autograd.Variable(x, requires_grad=True)
        return x

    def __predict_probabilities(self, x):
        x = x.to(self.device)
        pack_card_mask = x[..., -1].bool()
        y_logits = self.model(x)
        y_logits = y_logits[pack_card_mask]
        y_probs = torch.softmax(y_logits, dim=-1)
        return y_probs

    def __print_situation(self, pool_cards, pack_cards):
        situation_string = ""
        situation_string += "# Pool\n\n"
        for card, quantity in pool_cards.items():
            card = card.replace(" - ", "/")
            situation_string += f"{quantity} {card}\n"

        situation_string += "\n# Pack\n\n"
        for card, quantity in pack_cards.items():
            card = card.replace(" - ", "/")
            situation_string += f"{quantity} {card}\n"

        print(situation_string)

    def __print_predictions(self, pool_cards, pack_cards, picked_card, y_probs):
        prediction_string = ""
        y_probs = y_probs.cpu().detach().numpy()

        all_card_names = self.__get_all_card_names_in_order(pool_cards, pack_cards)
        for card, prob in zip(all_card_names[-len(y_probs):], y_probs):
            tally = int(100 * prob) * "#"
            prediction_string += f"{card:40} {tally}({prob:.2f})"
            if picked_card in card:
                prediction_string += " <-- Chosen by player"
            prediction_string += "\n"

        print(prediction_string)

    def __print_gradient_explainability(self, pool_cards, pack_cards, x, y_probs):
        all_card_names = self.__get_all_card_names_in_order(pool_cards, pack_cards)
        feature_names = self.card_preprocessor.get_feature_names() + ["is_pack_card"]
        for i in range(len(y_probs)):
            candidate_card_name = all_card_names[-len(y_probs) + i]
            candidate_card_prob = 100 * y_probs[i]
            gradient = torch.autograd.grad(y_probs[i], x, retain_graph=True)[0].cpu().detach().numpy()
            gradients_per_card_feature = {}
            for card_index in range(gradient.shape[0]):
                card_name = all_card_names[card_index]
                for feature_index in range(gradient.shape[1]):
                    feature_name = feature_names[feature_index]
                    gradient_component_name = f"{card_name} - {feature_name}"
                    gradients_per_card_feature[gradient_component_name] = gradient[card_index][feature_index]
            gradients_per_card_feature = pd.Series(gradients_per_card_feature)

            print(f"# Candidate card: '{candidate_card_name}' (predicted probability: {candidate_card_prob:.1f}%)")
            print(gradients_per_card_feature.loc[gradients_per_card_feature.abs().sort_values(ascending=False).iloc[:10].index])
            print()

    def __get_all_card_names_in_order(self, pool_cards, pack_cards):
        all_card_names = []
        for card, quantity in pool_cards.items():
            card = card.replace(" - ", "/")
            if quantity == 1:
                all_card_names.append(f"Pool - {card}")
            else:
                for n in range(quantity):
                    all_card_names.append(f"Pool - {card} ({n})")

        for card, quantity in pack_cards.items():
            card = card.replace(" - ", "/")
            if quantity == 1:
                all_card_names.append(f"Pack - {card}")
            else:
                for n in range(quantity):
                    all_card_names.append(f"Pack - {card} ({n})")

        return all_card_names
