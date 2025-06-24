import logging
import os
from typing import Any, Dict, List

import pandas as pd
import torch
from transformers import (AutoModelForSequenceClassification, Trainer,
                          TrainingArguments)

# Set User-Agent for transformers library
os.environ.setdefault(
    "USER_AGENT", "FoodSave-AI/1.0.0 (https://github.com/foodsave-ai)"
)

logger = logging.getLogger(__name__)


class IntentDataset(torch.utils.data.Dataset):
    def __init__(self, encodings: Dict[str, Any], labels: List[int]) -> None:
        self.encodings = encodings
        self.labels = labels

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
        item["labels"] = torch.tensor(self.labels[idx])
        return item

    def __len__(self) -> int:
        return len(self.labels)


class IntentTrainer:
    def __init__(
        self,
        tokenizer: Any,
        model_name: str = "distilbert-base-uncased",
        num_labels: int = 2,
    ) -> None:
        self.tokenizer = tokenizer
        self.model = AutoModelForSequenceClassification.from_pretrained(
            model_name, num_labels=num_labels
        )
        self.model_name = model_name

    def load_data(self, data_path: str) -> pd.DataFrame:
        """Ładuje dane treningowe z pliku CSV."""
        df = pd.read_csv(data_path)
        if "text" not in df.columns or "intent" not in df.columns:
            raise ValueError("CSV must contain 'text' and 'intent' columns.")
        return df

    def prepare_data(
        self, df: pd.DataFrame, label_map: Dict[str, int]
    ) -> "IntentDataset":
        """Przygotowuje dane do treningu (tokenizacja, mapowanie etykiet)."""
        texts = df["text"].tolist()
        labels = [label_map[intent] for intent in df["intent"].tolist()]

        encodings = self.tokenizer(texts, truncation=True, padding=True, max_length=128)

        return IntentDataset(encodings, labels)

    def train(
        self, train_dataset: Any, val_dataset: Any, output_dir: str = "./results"
    ) -> Dict[str, Any]:
        """Trenuje model klasyfikacji intencji."""
        logging_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=3,  # liczba epok
            per_device_train_batch_size=16,  # batch size na urządzenie (GPU/CPU)
            per_device_eval_batch_size=64,  # batch size na urządzenie (GPU/CPU)
            warmup_steps=500,  # liczba kroków rozgrzewki dla planisty learning rate
            weight_decay=0.01,  # siła weight decay
            logging_dir=f"{output_dir}/logs",  # katalog do logów TensorBoard
            logging_steps=100,
            eval_strategy="epoch",
            save_strategy="epoch",
            load_best_model_at_end=True,
            metric_for_best_model="eval_loss",
            report_to="none",  # Nie zgłaszaj do TensorBoard domyślnie
        )

        trainer = Trainer(
            model=self.model,
            args=logging_args,
            train_dataset=train_dataset,
            eval_dataset=val_dataset,
        )

        logger.info("Starting model training...")
        trainer.train()
        logger.info("Training complete. Evaluating model...")

        eval_results = trainer.evaluate()
        logger.info(f"Evaluation results: {eval_results}")

        # Zapisz model
        self.model.save_pretrained(output_dir)
        self.tokenizer.save_pretrained(output_dir)
        logger.info(f"Model saved to {output_dir}")
        return dict(eval_results)

    def create_label_map(self, intents: List[str]) -> Dict[str, int]:
        """Tworzy mapowanie etykiet tekstowych na ID numeryczne."""
        return {intent: i for i, intent in enumerate(sorted(list(set(intents))))}


# Przykład użycia:
# from backend.agents.ml_intent_detector import BERTIntentDetector
# from backend.ml_training.intent_trainer import IntentTrainer

# if __name__ == "__main__":
#     trainer = IntentTrainer(BERTIntentDetector().tokenizer)
#     df = trainer.load_data("data/intents.csv") # Wymaga pliku CSV z kolumnami 'text' i 'intent'

#     all_intents = df['intent'].unique().tolist()
#     label_map = trainer.create_label_map(all_intents)
#     trainer.model = AutoModelForSequenceClassification.from_pretrained(trainer.model_name, num_labels=len(all_intents))

#     full_dataset = trainer.prepare_data(df, label_map)
#     train_size = int(0.8 * len(full_dataset))
#     val_size = len(full_dataset) - train_size
#     train_dataset, val_dataset = torch.utils.data.random_split(full_dataset, [train_size, val_size))

#     asyncio.run(trainer.train(train_dataset, val_dataset, output_dir="./finetuned_intent_model"))
