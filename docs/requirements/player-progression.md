# Core Concept
Players go on adventures with a specific difficulty level, aiming to catch one or more Pokémon to complete them. The progression system will tie into catching Pokémon, earning XP, leveling up, and unlocking access to more interesting Pokémon as players advance.
Since catching Pokémon is based on player skill rather than a base catch chance, we’ll focus solely on chances for Pokémon to appear in adventures. Each adventure features 1 to 3 Pokémon, and their appearance depends on the player’s level and the adventure’s difficulty.

# 1. Pokémon Appearance System
Configuration per Pokémon

    Assign Pokémon to Tiers: Each Pokémon is categorized into a tier based on rarity and power:
        Tier 1: Common (e.g., Pidgey, Rattata)
        Tier 2: Uncommon (e.g., Growlithe, Machop)
        Tier 3: Rare (e.g., Dratini, Eevee)
        Tier 4: Epic (e.g., Dragonair, Gengar)
        Tier 5: Legendary (e.g., Mew, Dragonite)
    This tier assignment is the only configuration needed per Pokémon.

Appearance Algorithm

    Player Level Unlocks Tiers: Higher player levels unlock access to higher tiers:
        Levels 1–10: Tier 1 only
        Levels 11–20: Tiers 1 and 2
        Levels 21–30: Tiers 1, 2, and 3
        Levels 31–40: Tiers 1 to 4
        Levels 41–50: Tiers 1 to 5
    Adventure Difficulty Modifies Chances: There are 7 difficulty levels (1 to 7), and higher difficulties increase the likelihood of encountering higher-tier Pokémon (within the tiers unlocked by the player’s level).
    Weighted Selection:
        Assign a base weight to each tier:
            Tier 1: 100
            Tier 2: 50
            Tier 3: 20
            Tier 4: 10
            Tier 5: 5
        Adjust weights based on difficulty using this formula:
        python

        adjusted_weight = base_weight[tier] * (1 + ((difficulty - 1) / 6) * (tier - 1))

        Where:
            base_weight[tier]: Base weight for the tier
            difficulty: Adventure difficulty (1 to 7)
            tier: Pokémon tier (1 to 5)
        This ensures Tier 1 weights remain unchanged, while higher tiers get a boost as difficulty increases.
    Selection Process:
        Filter the Pokémon pool to include only tiers unlocked by the player’s level.
        Calculate the adjusted weight for each eligible Pokémon based on its tier and the adventure’s difficulty.
        Randomly select 1 to 3 Pokémon using these adjusted weights (higher weights = higher chance).

This system ensures that Pokémon appearances scale with both player level and adventure difficulty, offering variety and progression.

# 2. XP Formula Matching RPG Progression Curves
The XP system should feel rewarding and align with progression curves in successful RPGs, avoiding overly simplistic linear growth. We’ll use an exponential curve with slight flattening to balance early progression and late-game effort.
XP Needed to Level Up

    Formula:
    python

    xp_needed = 100 * (1.2 ** (level - 1))

    Where:
        level: Current player level
        Base XP: 100 (XP needed from Level 1 to 2)
    This creates a 20% increase in XP required per level, mimicking exponential growth common in RPGs like Pokémon or Final Fantasy, while remaining achievable.

XP Granted

    Per Pokémon Caught (based on tier):
        Tier 1: 50 XP
        Tier 2: 100 XP
        Tier 3: 200 XP
        Tier 4: 400 XP
        Tier 5: 800 XP
    Bonus XP for Adventure Completion:
    python

    bonus_xp = 50 * difficulty

    Where:
        difficulty: Difficulty level (1 to 7)
    Total XP per Adventure:
    python

    total_xp = sum(xp_per_pokemon for pokemon in caught_pokemon) + 50 * difficulty

This ensures early levels are quick, while higher levels require sustained effort, matching typical RPG curves.

# 3. Decoupling Difficulty from Player Levels
Player levels (up to 50) and adventure difficulties (currently 7) are independent. The system must remain flexible if the number of difficulties changes.
Solution

    Player Level: Determines which Pokémon tiers are unlocked (see point 1).
    Difficulty: Affects:
        Pokémon appearance chances (via the adjusted weight formula).
        Bonus XP (via 50 * difficulty).
    Flexibility: The formulas use difficulty as a variable, so changing the number of difficulties (e.g., to 10) requires no adjustments—just update the range of difficulty. The system scales automatically.

This decoupling allows players to choose their challenge level independently of progression, with rewards scaling accordingly.

# 4. Automatic Accommodation of Pokémon Database
The system should handle any number of Pokémon without manual formula tweaks, only requiring tier assignment.
Solution

    Tier-Based Design: Since Pokémon are assigned to tiers, and the appearance algorithm uses tier weights, adding new Pokémon only involves:
        Assigning them a tier (e.g., new Pokémon “X” as Tier 3).
        Adding them to the database.
    Scalability: The weighted selection process automatically incorporates new Pokémon based on their tier, with no need to adjust equations.

This ensures flexibility and ease of expansion.

# 5. Adjusting Chances
To fine-tune Pokémon appearance chances:

    Current Formula:
    python

    adjusted_weight = base_weight[tier] * (1 + ((difficulty - 1) / 6) * (tier - 1))

        This moderately increases higher-tier chances as difficulty rises.
    Adjustment Option: For a stronger effect, modify the multiplier:
    python

    adjusted_weight = base_weight[tier] * (1 + 0.1 * difficulty * (tier - 1))

        This makes high-tier Pokémon more common at higher difficulties (e.g., at difficulty = 7, Tier 5’s multiplier becomes 1 + 0.1 * 7 * 4 = 3.8, significantly boosting its weight).
    Use the original formula for balance, or the alternative for a more rewarding difficulty curve.

# Summary of Equations

    Pokémon Appearance Chance:
        Adjusted Weight for a Pokémon in tier:
        python

        adjusted_weight = base_weight[tier] * (1 + ((difficulty - 1) / 6) * (tier - 1))

            base_weight[tier]: Base weight (Tier 1: 100, Tier 2: 50, Tier 3: 20, Tier 4: 10, Tier 5: 5)
            difficulty: Difficulty level (1 to 7)
            tier: Tier (1 to 5)
    XP Needed for Level-Up:
    python

    xp_needed = 100 * (1.2 ** (level - 1))

        level: Current player level
    XP Granted per Pokémon Caught:
        Tier 1: 50 XP
        Tier 2: 100 XP
        Tier 3: 200 XP
        Tier 4: 400 XP
        Tier 5: 800 XP
    Bonus XP for Adventure Completion:
    python

    bonus_xp = 50 * difficulty

        difficulty: Difficulty level
    Total XP per Adventure:
    python

    total_xp = sum(xp_per_pokemon for pokemon in caught_pokemon) + 50 * difficulty