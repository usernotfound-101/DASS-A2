# MoneyPoly White-Box Test Report

This report documents branch-focused white-box tests added in `tests/test_white_box.py`.

## How Tests Were Run

From project root:

```bash
cd moneypoly
/home/ayush/DASS/dass-a2/.venv/bin/python -m unittest discover -s tests -p "test_white_box.py" -v
```

## Test Cases, Why They Matter, and Issues Found

1. `test_dice_roll_includes_upper_bound_six`
- Why needed: Checks the dice branch that generates random values, including the max boundary.
- Key state/edge case: Largest legal die value (`6`).
- Issue found: Dice used `random.randint(1, 5)`, so `6` could never occur.
- Fix: Changed both dice calls to `random.randint(1, 6)`.
- Commit: `Error 1: Add white-box tests and fix dice roll upper bound`.

2. `test_player_move_passing_go_awards_salary`
- Why needed: Validates movement branch when wrapping around board end.
- Key state/edge case: Player at `39` moving `2` spaces (passes Go but does not land on `0`).
- Issue found: Salary was only granted when final position was exactly `0`.
- Fix: Grant salary when `old_position + steps >= BOARD_SIZE`.
- Commit: `Error 2: Award GO salary when passing board start`.

3. `test_buy_property_with_exact_balance_succeeds`
- Why needed: Verifies affordability decision branch in `buy_property`.
- Key state/edge case: Player balance exactly equals property price.
- Issue found: Condition used `<=`, wrongly blocking exact-balance purchase.
- Fix: Changed check to `<`.
- Commit: `Error 3: Allow property purchase at exact balance`.

4. `test_pay_rent_transfers_to_owner`
- Why needed: Covers non-mortgaged rent payment branch and ownership transfer behavior.
- Key state: Tenant and owner balances before/after rent.
- Issue found: Tenant paid rent, but owner did not receive it.
- Fix: Added `prop.owner.add_money(rent)`.
- Commit: `Error 4: Credit property owner when rent is paid`.

5. `test_jail_fine_branch_deducts_player_balance`
- Why needed: Covers jailed-player decision branch where player chooses to pay fine.
- Key state/edge case: Jail status transition with fine payment.
- Issue found: Bank collected fine, but player balance was not reduced.
- Fix: Added `player.deduct_money(JAIL_FINE)` before collecting to bank.
- Commit: `Error 5: Deduct player balance when paying jail fine`.

6. `test_find_winner_returns_highest_net_worth`
- Why needed: Covers winner-selection decision logic.
- Key state: Two players with different net worth values.
- Issue found: Code selected minimum net worth (`min`) instead of maximum.
- Fix: Replaced `min(...)` with `max(...)`.
- Commit: `Error 6: Select winner by highest net worth`.

7. `test_bank_collect_negative_amount_is_ignored`
- Why needed: Covers defensive branch for invalid bank input values.
- Key state/edge case: Negative amount passed to `collect`.
- Issue found: Negative values reduced bank funds despite docstring saying they are ignored.
- Fix: Early return when `amount <= 0`.
- Commit: `Error 7: Ignore non-positive amounts in bank collect`.

8. `test_bank_give_loan_reduces_bank_funds`
- Why needed: Covers loan issuance path and shared bank/player state consistency.
- Key state: Bank and player balances after loan.
- Issue found: Loan increased player balance but did not decrease bank funds.
- Fix: `give_loan` now uses `pay_out` and then credits player.
- Commit: `Error 8: Reduce bank reserves when issuing loans`.

## Final Result

- Total white-box tests added: `8`
- Initial failing tests: `8/8`
- Final passing tests: `8/8`
- All identified logic issues above were fixed in iterative commits.
