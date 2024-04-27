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

## Scrape stats from 17lands.com
```
mtgc 17lands enrich_card --card_json_path "data/my_collection/cards/*.json" --seventeen_lands_folder data/17lands
```
