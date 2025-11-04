# NFL Data Formatting Standards

This document defines the formatting standards for all NFL agents (agent004-007) to ensure consistent, user-friendly data presentation.

## Overview

All NFL agents must follow these formatting standards when presenting data to users. The `nfl_formatters.py` module provides utility functions to implement these standards consistently.

## Requirements Mapping

These formatting standards implement the following requirements from the design document:

- **Requirement 9.1**: Date/time formatting in user-friendly formats
- **Requirement 9.2**: Team name formatting with full names and abbreviations
- **Requirement 9.3**: Score highlighting and game status formatting
- **Requirement 9.4**: Structured list formatting for multi-item responses
- **Requirement 9.5**: Position-aware statistics formatting

## Formatting Standards

### 1. Date and Time Formatting (Requirement 9.1)

**Standard Format**: `Day, Month DD, YYYY at HH:MM AM/PM TZ`

**Examples**:
- `Sunday, January 15, 2025 at 4:30 PM EST`
- `Monday, December 25, 2024 at 8:15 PM EST`
- `Thursday, November 28, 2024 at 12:30 PM EST`

**Implementation**:
```python
from nfl_formatters import format_datetime

formatted = format_datetime("2025-01-15T21:30Z", timezone="US/Eastern", include_day=True)
# Output: "Sunday, January 15, 2025 at 4:30 PM EST"
```

**Rules**:
- Always include day of week for game times
- Use full month names (January, not Jan)
- Include timezone abbreviation (EST, EDT, CST, etc.)
- Default to US/Eastern timezone unless specified
- Convert from UTC/ISO format to local time

### 2. Team Name Formatting (Requirement 9.2)

**Standard Format**: `Full Team Name (ABBREVIATION)`

**Examples**:
- `Dallas Cowboys (DAL)`
- `Philadelphia Eagles (PHI)`
- `Kansas City Chiefs (KC)`
- `San Francisco 49ers (SF)`

**Implementation**:
```python
from nfl_formatters import format_team_name

formatted = format_team_name("Dallas Cowboys", "DAL")
# Output: "Dallas Cowboys (DAL)"
```

**Rules**:
- Always include full team name
- Always include abbreviation in parentheses
- Use official ESPN team abbreviations
- Maintain consistent spacing

### 3. Matchup Formatting

**Standard Format**: 
- Away @ Home: `Team A (ABR) @ Team B (ABR)`
- Neutral Site: `Team A (ABR) vs Team B (ABR)`

**Examples**:
- `Dallas Cowboys (DAL) @ Philadelphia Eagles (PHI)`
- `Kansas City Chiefs (KC) vs San Francisco 49ers (SF)` (neutral site)

**Implementation**:
```python
from nfl_formatters import format_matchup

# Regular game
matchup = format_matchup("Dallas Cowboys (DAL)", "Philadelphia Eagles (PHI)")
# Output: "Dallas Cowboys (DAL) @ Philadelphia Eagles (PHI)"

# Neutral site
matchup = format_matchup("Team A", "Team B", is_neutral=True)
# Output: "Team A vs Team B"
```

**Rules**:
- Use `@` symbol for away @ home games
- Use `vs` for neutral site games (Super Bowl, international games)
- Away team always listed first

### 4. Score Display and Highlighting (Requirement 9.3)

**Standard Formats**:

**Completed Games**:
```
Final: [Winner] [Score], [Loser] [Score] ✓
```

**Live Games**:
```
Live - [Quarter], [Time] remaining
Current: [Team A] [Score], [Team B] [Score]
```

**Examples**:
- `Final: PHI 31, DAL 24 ✓`
- `Live - 3rd Quarter, 8:42 remaining`
- `Current: KC 21, BUF 17`

**Implementation**:
```python
from nfl_formatters import format_score_display, format_game_status

# Completed game
score = format_score_display(
    away_team="DAL",
    away_score=24,
    home_team="PHI",
    home_score=31,
    status="Final",
    is_completed=True,
    highlight_winner=True
)
# Output: "Final: PHI 31, DAL 24 ✓"

# Live game status
status = format_game_status(
    status_type="In Progress",
    period=3,
    clock="8:42",
    is_completed=False
)
# Output: "Live - 3rd Quarter, 8:42 remaining"
```

**Rules**:
- For completed games, show winner first with checkmark (✓)
- For live games, show quarter and time remaining
- Use "Final" for completed games
- Use "Live - [Quarter]" for in-progress games
- Show "Overtime" for period 5
- Handle ties appropriately

### 5. Venue Formatting

**Standard Format**: `📍 Venue Name (City, State)`

**Examples**:
- `📍 AT&T Stadium (Arlington, TX)`
- `📍 Lincoln Financial Field (Philadelphia, PA)`
- `📍 Arrowhead Stadium (Kansas City, MO)`

**Implementation**:
```python
from nfl_formatters import format_venue

venue = format_venue("AT&T Stadium", "Arlington", "TX")
# Output: "📍 AT&T Stadium (Arlington, TX)"
```

**Rules**:
- Always use 📍 emoji prefix
- Include city and state when available
- Use state abbreviations (TX, PA, MO)
- If city/state unavailable, show venue name only

### 6. Broadcast Network Formatting

**Standard Format**: `📺 Network Name`

**Examples**:
- `📺 NBC Sunday Night Football`
- `📺 ESPN Monday Night Football`
- `📺 CBS`
- `📺 Amazon Prime Video`

**Implementation**:
```python
from nfl_formatters import format_broadcast_network

network = format_broadcast_network("NBC Sunday Night Football")
# Output: "📺 NBC Sunday Night Football"
```

**Rules**:
- Always use 📺 emoji prefix
- Include full broadcast name when available
- Common networks: CBS, FOX, NBC, ESPN, NFL Network, Amazon Prime

### 7. Structured List Formatting (Requirement 9.4)

**Standard Format**:
```
🏈 [Title]

[Item 1]

[Item 2]

[Item 3]
```

**Example**:
```
🏈 NFL Scores - Week 18

Dallas Cowboys (DAL) @ Philadelphia Eagles (PHI)
Final: PHI 31, DAL 24 ✓
📍 Lincoln Financial Field

Kansas City Chiefs (KC) vs Buffalo Bills (BUF)
Live - 3rd Quarter, 8:42 remaining
Current: KC 21, BUF 17
📍 Arrowhead Stadium
```

**Implementation**:
```python
from nfl_formatters import format_structured_list

games = [
    {"content": "Game 1 details..."},
    {"content": "Game 2 details..."}
]

formatted = format_structured_list(games, title="NFL Scores - Week 18")
```

**Rules**:
- Use 🏈 emoji for title
- Separate items with blank lines
- Group related items (by date, week, team)
- Use consistent indentation
- List chronologically when applicable

### 8. Player Statistics Formatting (Requirement 9.5)

**Position-Specific Formats**:

**Quarterbacks (QB)**:
```
Passing: [yards] yards, [TDs] TDs, [INTs] INTs
Completion: [%]% | QB Rating: [rating]
Rushing: [yards] yards, [TDs] TDs (if significant)
```

**Running Backs (RB)**:
```
Rushing: [yards] yards, [TDs] TDs, [YPC] YPC
Receiving: [rec] rec, [yards] yards, [TDs] TDs
```

**Wide Receivers/Tight Ends (WR/TE)**:
```
Receiving: [rec] rec, [yards] yards, [TDs] TDs
Avg: [YPR] yards/rec | Targets: [targets]
```

**Kickers (K)**:
```
Field Goals: [made]/[att] ([%]%)
Extra Points: [made] | Long: [yards] yards
```

**Defensive Players**:
```
Tackles: [total] | Sacks: [sacks] | Interceptions: [ints]
```

**Implementation**:
```python
from nfl_formatters import format_player_stats_by_position

qb_stats = {
    "passingYards": 4183,
    "passingTouchdowns": 32,
    "interceptions": 11,
    "completionPct": 67.2,
    "qbRating": 98.5
}

formatted = format_player_stats_by_position("QB", qb_stats)
# Output: "Passing: 4,183 yards, 32 TDs, 11 INTs | Completion: 67.2% | QB Rating: 98.5"
```

**Rules**:
- Format numbers with comma separators for thousands (4,183 not 4183)
- Use position-appropriate statistics
- Use pipe separators (|) between stat categories
- Show per-game averages when relevant
- Include season context (e.g., "through Week 17")

## Complete Examples

### Complete Game Display

```
Dallas Cowboys (DAL) @ Philadelphia Eagles (PHI)
Sunday, January 15, 2025 at 4:30 PM EST
Final: PHI 31, DAL 24 ✓
📍 Lincoln Financial Field (Philadelphia, PA)
📺 NBC Sunday Night Football
```

### Complete Player Stats Display

```
🏈 NFL Player Statistics

**Patrick Mahomes** - Kansas City Chiefs (KC) (QB)

Passing: 4,183 yards, 32 TDs, 11 INTs
Completion: 67.2% | QB Rating: 98.5
Rushing: 389 yards, 2 TDs

Season: 2024 (through Week 17)
```

### Complete Schedule Display

```
📅 Dallas Cowboys Schedule - Week 19 (Playoffs)

Sunday, January 21, 2025 at 4:30 PM EST
Dallas Cowboys (DAL) @ San Francisco 49ers (SF)
📍 Levi's Stadium (Santa Clara, CA)
📺 FOX
```

## Agent-Specific Guidelines

### agent004 (NFL Scores)
- Focus on score highlighting and game status
- Show multiple games in structured lists
- Include venue and broadcast info when relevant

### agent005 (NFL Schedule)
- Emphasize date/time formatting
- Show venue and broadcast network
- Group games by date or week

### agent006 (NFL Player Stats)
- Use position-aware formatting
- Format numbers with comma separators
- Show relevant stats only for each position

### agent007 (NFL Predictions)
- Use team name formatting consistently
- Format predicted scores clearly
- Include date/time for upcoming games
- Present statistics in structured format

## Testing

See `nfl_formatters_examples.py` for usage examples and test cases.

## Dependencies

- `pytz`: For timezone conversions (added to all agent requirements.txt)

## Maintenance

When updating formatting standards:
1. Update `nfl_formatters.py` utility functions
2. Update agent system prompts
3. Update this documentation
4. Update examples file
5. Test with all agents
