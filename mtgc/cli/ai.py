import os
import json
import random

import pandas as pd
from catboost import CatBoostClassifier

from mtgc.feature_engineering import CardPairFeatureExtractor


class AICLI:
    def create_dataset(self, deck_folder: str, n_samples_per_deck: int, output_path: str):
        deck_json_dict_list = self.__load_decks(folder_path=deck_folder)
        dataset = self.__create_dataset_from_decks(deck_json_dict_list, n_samples_per_deck=n_samples_per_deck)
        print(f"Saving dataset to '{output_path}'")
        dataset.to_csv(output_path, index=False)

    def __load_decks(self, folder_path: str):
        deck_json_dict_list = []
        deck_filenames = os.listdir(folder_path)
        for filename in deck_filenames:
            path = os.path.join(folder_path, filename)
            deck_json_dict = self.__load_deck(path)
            deck_json_dict_list.append(deck_json_dict)
        return deck_json_dict_list

    def __load_deck(self, path: str):
        with open(path, "r") as f:
            deck_json_dict = json.load(f)
        return deck_json_dict

    def __create_dataset_from_decks(self, deck_json_dict_list, n_samples_per_deck: int):
        dataset = []
        for n, deck_json_dict in enumerate(deck_json_dict_list):
            print(f"Create dataset from deck {n+1}/{len(deck_json_dict_list)}")
            cards = deck_json_dict["cards"]
            for _ in range(n_samples_per_deck // 2):
                # Create one positive pair
                card_1 = random.choice(cards)["name"]
                card_2 = random.choice([card for card in cards if card != card_1])["name"]
                dataset.append({
                    "card_1": card_1,
                    "card_2": card_2,
                    "label": 1
                })

                # Create one negative pair
                other_deck_json_dict = deck_json_dict_list[random.choice([i for i in range(len(deck_json_dict_list)) if i != n])]
                other_deck_cards = other_deck_json_dict["cards"]
                card_2 = random.choice(other_deck_cards)["name"]
                dataset.append({
                    "card_1": card_1,
                    "card_2": card_2,
                    "label": 0
                })

        return pd.DataFrame(dataset)

    def train(self, dataset_path: str, card_folder_path: str, output_path: str):
        df = pd.read_csv(dataset_path)

        print("===== Preprocess dataset =====")
        dataset = self.__preprocess(df, card_folder_path=card_folder_path)
        training_dataset, validation_dataset = self.__split_dataset(dataset)

        print("===== Training =====")
        model = self.__train_catboost(training_dataset)

        print("===== Evaluation =====")
        metrics = self.__evaluate(model, training_dataset, validation_dataset)
        print(f"Metrics: {metrics}")

        print("===== Saving model =====")
        model.save_model(output_path, format="cbm")
        print(f"Model saved to '{output_path}'")

    def __preprocess(self, df: pd.DataFrame, card_folder_path: str) -> pd.DataFrame:
        feature_extractor = CardPairFeatureExtractor()
        df = df[df["card_1"] != df["card_2"]].reset_index(drop=True)
        dataset = []
        for n, row in df.iterrows():
            print(f"{n+1}/{len(df)}")
            card_filename_1 = row["card_1"].replace("/", " - ")
            card_path_1 = os.path.join(card_folder_path, f"{card_filename_1}.json")
            card_filename_2 = row["card_2"].replace("/", " - ")
            card_path_2 = os.path.join(card_folder_path, f"{card_filename_2}.json")

            with open(card_path_1, "r") as f:
                card_json_dict_1 = json.load(f)
            with open(card_path_2, "r") as f:
                card_json_dict_2 = json.load(f)

            features = feature_extractor.extract(card_json_dict_1, card_json_dict_2)

            dataset.append(features)
        dataset = pd.DataFrame(dataset)
        dataset["label"] = df["label"]
        return dataset

    def __split_dataset(self, dataset: pd.DataFrame):
        split_index = int(0.80 * len(dataset))
        training_dataset = dataset.iloc[:split_index]
        validation_dataset = dataset.iloc[split_index:]
        return training_dataset, validation_dataset

    def __train_catboost(self, training_dataset: pd.DataFrame):
        model = CatBoostClassifier(n_estimators=1000)
        model.fit(
            X=training_dataset.drop("label", axis=1),
            y=training_dataset["label"]
        )
        return model

    def __evaluate(self, model, training_dataset, validation_dataset):
        training_predictions = model.predict(training_dataset.drop("label", axis=1))
        validation_predictions = model.predict(validation_dataset.drop("label", axis=1))

        return {
            "training_accuracy": (training_predictions == training_dataset["label"]).mean(),
            "validation_accuracy": (validation_predictions == validation_dataset["label"]).mean()
        }
