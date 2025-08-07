# EDHPodAnalyzer
Commander/EDH deck analyzer for 4-person pods

REQUIREMENTS TO RUN:
--------------------------
YOU MUST DOWNLOAD A LOCAL COPY OF THE LATEST BULK DATA FILE FROM https://scryfall.com/docs/api/bulk-data
The Oracle Cards are good enough, but default cards should work as well.
EDIT EVALUATOR.PY TO OPEN THE FILE YOU DOWNLOAD.
These files can be quite large, so be aware.

DEPENDENCIES:
--------------------------
  pip install rich

from rich.console import Console

from rich.table import Table

from rich.text import Text

  pip install pyedhrec (currently unusued)

from pyedhrec import EDHRec

USAGE:
---------------------------
python evaluator.py deck1.txt deck2.txt deck3.txt deck4.txt

Or any other text files containing MTGO-formated Commander Decks. I use https://moxfield.com/
Several sample decks are included by default (decks1 - 9)
