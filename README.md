# magic-the-gathering-collection
A set of CLI tools to manage my collection and build decks.

## Add new card
```
mtgc card add "On the job"
```

## Import cards from existing decks
```
mtgc card add_from_decks --deck_folder data/mtgdecks/decks/ --output_folder_path data/mtgdecks/cards
```

## Add cards to deck
### One card
```
mtgc deck add --deck mtgc_data/decks/Detective.json --card mtgc_data/cards/Branch\ of\ Vitu-Ghazi.json
```

### Multiple cards
```
mtgc deck add --deck mtgc_data/decks/Detective.json --card "mtgc_data/cards/*"
```

## Scrape decks from mtgdecks.net
```
mtgc mtgdecks scrape --max_n_decks 100 --output_data_folder data/mtgdecks/decks --format "Modern"
```

## Scrape stats from 17lands.com
```
mtgc 17lands enrich_card --card_json_path "data/my_collection/cards/*.json" --seventeen_lands_folder data/17lands
```

## AI (for autodraft)
### Create dataset
```
mtgc ai create_dataset --deck_folder data/mtgdecks/decks --n_samples_per_deck 100 --output_path data/mtgdecks/dataset.csv
```

### Train card compatibility classifier
```
mtgc ai train --dataset_path data/mtgdecks/dataset.csv --card_folder_path data/mtgdecks/cards --output_path models/card_compatibility_classifier.cbm
```

### Autodraft (predict most compatible cards from collection for a given deck)
```
mtgc ai autodraft --deck_path data/my_collection/decks/Detective.json --card_folder_path data/my_collection/cards --model_path models/card_compatibility_classifier.cbm
```
