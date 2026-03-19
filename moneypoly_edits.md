game.py edits:
Unnecessary parenthesis after 'not' keyword.
Final new line added
Added Docstring at the top
Removed f string which didnt have any interpolated variables
Removed unnecessary elif after break, so it became aif and then if
Removed unused import os
Removed unused GO_TO_JAIL_POSITION
Added 3 new functions to set the initial game state, `set_board_bank_die`, `set_values` and `set_cards`
All function/methods in game.py now have docstrings, pointless string statements are removed, and all attributes are initialized in init.

Iteration 18: Reduced Game instance attributes via TurnState
- Added TurnState dataclass in game.py to hold current_index, turn_number, and running.
- Replaced direct Game fields with self.state references in current_player, advance_turn, play_turn, _check_bankruptcy, set_values, and run.
- Goal: resolve too-many-instance-attributes warning in game.py while preserving behavior.