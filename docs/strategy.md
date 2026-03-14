TQQQ/SQQQ 3‑Block Strategy
Reactive, Percentile‑Based, Multi‑Day Leveraged ETF System

1. Overview

This document describes a reactive, percentile‑based, multi‑day accumulation strategy for trading leveraged ETFs (TQQQ and SQQQ).

The system uses:
• 	Nasdaq daily direction
• 	Percentile‑based entry levels
• 	A 3‑block capital architecture
• 	Gain‑target or percentile exits

The strategy is designed to:
• 	buy deeper during multi‑day streaks
• 	reduce average cost through structured block entries
• 	exit on statistically reliable rebounds
• 	avoid stop‑losses that disrupt cycle completion
• 	maintain discipline and risk control through block sizing

2. Capital Architecture:

Total capital is divided into 3 equal blocks.
Example:
Total: $1,200  
Block 1: $400  
Block 2: $400  
Block 3: $400

Why 3 blocks?
Based on 60‑day Nasdaq streak analysis:
- 1–2 day streaks = common
- 3‑day streaks = occasional
- 4+ day streaks = rare

Three blocks allow the system to:
- buy during 1‑day streaks
- buy during 2‑day streaks
- buy during 3‑day streaks
- avoid overexposure during rare 4+ day streaks

This is the core risk‑management mechanism.

3. Market Signal (Nasdaq Direction)

The system uses daily Nasdaq close to determine direction:
- Nasdaq UP → Buy SQQQ
- Nasdaq DOWN → Buy TQQQ
This ensures the strategy is always aligned with short‑term market movement.

4. Entry Logic (Percentile‑Based)

Each day, the system calculates the 15th percentile entry price for the appropriate ETF (TQQQ or SQQQ).
This becomes the entry price for that day.
Entry Ladder
- Day 1 → Entry Price 1
- Day 2 → Entry Price 2
- Day 3 → Entry Price 3
Rule:
Each new entry price must be lower than the previous one.
This ensures:
- improved average cost
- safer accumulation
- easier exits on rebound


5. Block Buy Ladder

You buy one block per day only if:
- The Nasdaq signal matches the direction
- The new entry price is lower than the previous entry
- You still have unused blocks

This creates a controlled 3‑step ladder:
- Block 1 → shallow dip
- Block 2 → deeper dip
- Block 3 → deepest dip

This ladder is the engine that reduces average cost and increases exit probability.

6. Exit Logic

The system exits using whichever condition triggers first:
A) Gain‑Target Exit
- Typically +1.5% to +2.0%
- Fast, reliable, frequent
- Works extremely well after multi‑day streaks

B) Percentile Exit
- Typically 60th–75th percentile
- Less frequent
- Larger gains
- Used when the market rebounds strongly

The system is reactive — it takes whichever exit comes first

7. No More Buys After 3 Blocks

If the Nasdaq streak continues:
- Day 4 UP or DOWN → no more buys
- You are fully allocated
- You hold and wait for the rebound exit

This protects the system from rare streaks and prevents overexposure.

8. Order Execution (Broker Workflow)

Buy Orders
- Use limit buy at the daily entry price
- If price hits → order fills
- If not → no fill (correct behavior)

Sell Orders
- Use limit sell at the exit price
- Good‑til‑day or good‑til‑canceled
- Do NOT use trailing stops
- Trailing stops will sell during normal dips
- They break the cycle and reduce expectancy

9. Drawdown Handling

The system does not use stop‑losses.
Why?
- Leveraged ETFs rebound strongly
- Block averaging reduces cost
- Stop‑losses often trigger before the rebound
- The 3‑block architecture is the risk‑control mechanism

The system is designed to survive streaks, not avoid them.

10. Real‑World Testing Process

The strategy is validated through live observation:
- Day 1: Nasdaq DOWN → Block 1
- Day 2: Nasdaq DOWN → Block 2
- Day 3: Observe (DOWN → Block 3, UP → prepare for exit)

This real‑world testing confirms:
- streak behavior
- entry accuracy
- block depth
- rebound strength
- exit reliability

11. Summary

This strategy is:
- reactive, not predictive
- statistical, not emotional
- structured, not discretionary
- risk‑controlled through block sizing
- profitable through disciplined exits

It buys deeper during streaks, exits on rebounds, and uses the 3‑block architecture as its risk‑management backbone.




