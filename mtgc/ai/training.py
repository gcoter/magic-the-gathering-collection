import os
import json
from pathlib import Path
from typing import Dict

import torch
import numpy as np
import pandas as pd

from mtgc.ai.data import load_cards_data, load_draft_data
from mtgc.ai.dataset import DraftDataset
from mtgc.ai.model import DraftPicker
from mtgc.ai.preprocessing import CardPreprocessor, filter_draft_data


class DraftTrainer:
    def __init__(
        self,
        card_preprocessor: CardPreprocessor,
        hyper_parameters: Dict,
        validation_proportion: float = 0.2,
        n_epochs = 10,
        n_cumulation_steps = 100,
        learning_rate = 1e-4,
    ):
        self.card_preprocessor = card_preprocessor
        self.hyper_parameters = hyper_parameters
        self.validation_proportion = validation_proportion
        self.n_epochs = n_epochs
        self.n_cumulation_steps = n_cumulation_steps
        self.learning_rate = learning_rate
        self.device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")

    def run(self, draft_data_path: str, draft_data_dtypes_path: str, card_folder: str, output_folder: str):
        draft_data_df = load_draft_data(draft_data_path, draft_data_dtypes_path)
        cards_data_dict = load_cards_data(card_folder)
        draft_data_df = filter_draft_data(draft_data_df, cards_data_dict)
        training_draft_dataset, validation_draft_dataset = self.__create_datasets(draft_data_df, cards_data_dict)
        model = self.__initialize_model()
        optimizer = self.__initialize_optimizer(model)
        self.__run_training_loop(
            model,
            training_draft_dataset,
            validation_draft_dataset,
            optimizer,
            output_folder
        )

    def __create_datasets(self, draft_data_df, cards_data_dict):
        draft_dataset = DraftDataset(
            draft_data_df=draft_data_df,
            cards_data_dict=cards_data_dict,
            card_preprocessor=self.card_preprocessor
        )
        training_draft_dataset, validation_draft_dataset = torch.utils.data.random_split(
            draft_dataset, [1 - self.validation_proportion, self.validation_proportion]
        )
        return training_draft_dataset, validation_draft_dataset

    def __initialize_model(self):
        print(f"Initialize model with hyper-parameters: {self.hyper_parameters}")
        model = DraftPicker(
            **self.hyper_parameters
        ).to(self.device)
        return model

    def __initialize_optimizer(self, model):
        return torch.optim.Adam(
            model.parameters(),
            lr=self.learning_rate,
        )

    def __run_training_loop(self, model, training_draft_dataset, validation_draft_dataset, optimizer, output_folder):
        print("Start training")

        training_cumulated_loss = 0.0
        n_steps_since_last_cumulation = 0
        training_draft_dataset_indices = np.arange(len(training_draft_dataset))
        loss_history = {"step": [], "training_loss": []}
        validation_metrics_history = []

        for n in range(self.n_epochs):
            print(f"===== Epoch {n + 1}/{self.n_epochs} =====")
            model.train()
            np.random.shuffle(training_draft_dataset_indices)
            for i, training_draft_dataset_index in enumerate(training_draft_dataset_indices):
                x, y = training_draft_dataset[training_draft_dataset_index]
                x = x.to(self.device)
                y = y.to(self.device)
                y_logits = model(x)

                pack_card_mask = x[..., -1].bool()
                y = y[pack_card_mask]
                y_logits = y_logits[pack_card_mask]

                loss = torch.nn.functional.cross_entropy(y_logits, y)
                training_cumulated_loss += loss.cpu().detach().numpy()
                n_steps_since_last_cumulation += 1
                loss.backward()

                if (i > 0 and i % self.n_cumulation_steps == 0) or (i == len(training_draft_dataset_indices) - 1):
                    training_cumulated_loss = training_cumulated_loss / n_steps_since_last_cumulation
                    loss_history["step"].append(n * len(training_draft_dataset_indices) + i)
                    loss_history["training_loss"].append(training_cumulated_loss)
                    print(f"{i}/{len(training_draft_dataset)}: {training_cumulated_loss:.4f}")
                    optimizer.step()
                    optimizer.zero_grad()
                    training_cumulated_loss = 0.0
                    n_steps_since_last_cumulation = 0

            print(f"***** Validation (epoch {n + 1}/{self.n_epochs}) *****")
            validation_metrics_history.append({
                "epoch": n,
                **self.__run_validation_loop(model, validation_draft_dataset)
            })

            print("***** Save model and metrics *****")
            self.__save_everything(model, loss_history, validation_metrics_history, output_folder)

    def __run_validation_loop(self, model, validation_draft_dataset):
        correct_count = 0
        random_correct_count = 0
        model.eval()

        for i, (x, y) in enumerate(validation_draft_dataset):
            if i > 0 and i % 1000 == 0:
                print(f"{i}/{len(validation_draft_dataset)}")

            x = x.to(self.device)
            y = y.to(self.device)
            y_logits = model(x)

            pack_card_mask = x[..., -1].bool()
            y = y[pack_card_mask]
            y_logits = y_logits[pack_card_mask]

            if torch.argmax(y_logits) == torch.argmax(y):
                correct_count += 1

            if torch.randint(len(y), size=(1,))[0] == torch.argmax(y):
                random_correct_count += 1

        validation_accuracy = correct_count / len(validation_draft_dataset)
        random_validation_accuracy = random_correct_count / len(validation_draft_dataset)
        print(f"Validation Accuracy: {100 * validation_accuracy:.1f}% (random: {100 * random_validation_accuracy:.1f}%)")

        validation_metrics = {
            "Validation Accuracy": validation_accuracy,
            "Random Validation Accuracy": random_validation_accuracy
        }

        return validation_metrics

    def __save_everything(self, model, loss_history, validation_metrics_history, output_folder):
        loss_history = pd.DataFrame(loss_history)
        validation_metrics_history = pd.DataFrame(validation_metrics_history)
        Path(output_folder).mkdir(parents=True, exist_ok=True)
        self.__save_model(model, output_folder)
        self.__save_hyper_parameters(output_folder)
        self.__save_loss_history(loss_history, output_folder)
        self.__save_metrics(validation_metrics_history, output_folder)

    def __save_model(self, model, output_folder: str):
        save_path = os.path.join(output_folder, "model.pt")
        print(f"Save model to '{save_path}'")
        torch.save(model.state_dict(), save_path)

    def __save_hyper_parameters(self, output_folder):
        save_path = os.path.join(output_folder, "hyper_parameters.json")
        print(f"Save hyper-parameters to '{save_path}'")
        with open(save_path, "w") as f:
            json.dump(self.hyper_parameters, f)

    def __save_loss_history(self, loss_history, output_folder: str):
        save_path = os.path.join(output_folder, "loss_history.csv")
        print(f"Save loss history to '{save_path}'")
        loss_history.to_csv(save_path, index=False)

    def __save_metrics(self, validation_metrics_history, output_folder):
        save_path = os.path.join(output_folder, "validation_metrics_history.csv")
        print(f"Save validation metrics to '{save_path}'")
        validation_metrics_history.to_csv(save_path, index=False)
