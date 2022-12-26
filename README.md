# Game jam discovery

This tool finds and dumps the highest ranked games from [itch.io](itch.io) game jams. 

[Game jams](https://itch.io/jams) are community-hosted events in which the hosts challenge developers to create themed games in a limited time window. The quality of the games created during jams varies tremendously, so hosts often review and rank each submitted games in order to find the best ones. Even though many of these games are quite fun and polished, they are mostly unmarketed and difficult to discover. Thus, many of the best games created during these jams go mostly unplayed.

I built this tool to identify and surface the top-ranked games from all past ranked game jams.

## How to use

First, create a python 3 environment using the requirements.txt file. 

If you just want to analyze data, I have provided a scrape as-of 2022-12-25. All of the game jams are in `jam_metadata.json`. The games from all ranked jams along with their "Overall" rankings are in `game_data.json`, and jams that were not ranked, had no submissions, or otherwise were not handled by the scraper's logic are in `invalid_jams.json` (this is approximately half of all jams). Feel free to use that file for analysis.

If you would like to regenerate the data yourself, there are two steps. First, scrape all of the historical game jam URLs using the `scrape_jam_urls` method in the `ItchioScraper` class. After you've scraped the jam names, set the `jam_fname` variable at the bottom of the `ItchioTools.py` file with your newly scraped game jam URLs and execute the file. This will scrape all games from the jam URLs that you provided. The program regularly checkpoints its results to a file, so just re-run the file if your connection is interrupted mid-scrape. This will produce a `game_data.json` file containing ranked games and `invalid_jams.json` containing jams that were not scraped.

## Ranking Methods

The `analyze_games.ipynb` notebook provides a simple solution for finding top games. By assuming that all games are drawn from the same distribution of quality, a game that falls in the top 5% of submitted games within a jam likely belongs to the top 5% of games overall. Thus, all games are assigned a score equal to their overall ranking divided by submissions, `overall_ranking/total_submissions`. For example, if a game was ranked first among 20 submissions, it has a rank score of 1/20 = 0.05. 

To get the best games, I simply choose a score threshold and select all games whose score is below that threshold. The top performers of big jams are likely to be better, so this method allows more games from large jams and fewer games from small jams. Still, some jams are quite large, so I capped the number of admissible games per jam at 20. 

## Just want to play the games?

You can find a spreadsheet with the top 5% of games, capped at 20 games per jam, [here](https://docs.google.com/spreadsheets/d/1QgVXITS6IgSllfWM6VryZIQeZEpf9wyk-JAtXkZbXUw/edit#gid=115223568). Most of these are video games, and most are free, but YMMV - you may find some paid games or TTRPGs among these!

You can also find this list in json and csv format in `best_games/best_games.json` and `best_games/best_games.csv`.

## TODO and known issues

* Currently, this program does not scrape unranked game jams. Eventually it should!
