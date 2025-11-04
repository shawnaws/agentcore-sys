"""
Examples of using NFL formatting utilities

This file demonstrates how to use the nfl_formatters module
for consistent data formatting across NFL agents.
"""

from nfl_formatters import (
    format_datetime,
    format_team_name,
    format_score_display,
    format_game_status,
    format_structured_list,
    format_player_stats_by_position,
    format_venue,
    format_broadcast_network,
    format_matchup
)


def example_score_formatting():
    """Example: Formatting NFL game scores"""
    
    # Format team names
    away_team = format_team_name("Dallas Cowboys", "DAL")
    home_team = format_team_name("Philadelphia Eagles", "PHI")
    
    # Format matchup
    matchup = format_matchup(away_team, home_team)
    print(matchup)
    # Output: Dallas Cowboys (DAL) @ Philadelphia Eagles (PHI)
    
    # Format completed game score
    score = format_score_display(
        away_team="DAL",
        away_score=24,
        home_team="PHI",
        home_score=31,
        status="Final",
        is_completed=True,
        highlight_winner=True
    )
    print(score)
    # Output: Final: PHI 31, DAL 24 ✓
    
    # Format live game status
    status = format_game_status(
        status_type="In Progress",
        period=3,
        clock="8:42",
        is_completed=False
    )
    print(status)
    # Output: Live - 3rd Quarter, 8:42 remaining


def example_schedule_formatting():
    """Example: Formatting NFL schedules"""
    
    # Format game date/time
    game_time = format_datetime(
        "2025-01-21T21:30Z",
        timezone="US/Eastern",
        include_day=True
    )
    print(game_time)
    # Output: Sunday, January 21, 2025 at 4:30 PM EST
    
    # Format venue
    venue = format_venue(
        "AT&T Stadium",
        city="Arlington",
        state="TX"
    )
    print(venue)
    # Output: 📍 AT&T Stadium (Arlington, TX)
    
    # Format broadcast network
    network = format_broadcast_network("NBC Sunday Night Football")
    print(network)
    # Output: 📺 NBC Sunday Night Football


def example_player_stats_formatting():
    """Example: Formatting player statistics"""
    
    # Quarterback stats
    qb_stats = {
        "passingYards": 4183,
        "passingTouchdowns": 32,
        "interceptions": 11,
        "completionPct": 67.2,
        "qbRating": 98.5,
        "rushingYards": 389,
        "rushingTouchdowns": 2
    }
    
    formatted_qb = format_player_stats_by_position("QB", qb_stats)
    print(formatted_qb)
    # Output: Passing: 4,183 yards, 32 TDs, 11 INTs | Completion: 67.2% | QB Rating: 98.5 | Rushing: 389 yards, 2 TDs
    
    # Running back stats
    rb_stats = {
        "rushingYards": 1463,
        "rushingTouchdowns": 13,
        "yardsPerCarry": 4.8,
        "receptions": 45,
        "receivingYards": 392,
        "receivingTouchdowns": 2
    }
    
    formatted_rb = format_player_stats_by_position("RB", rb_stats)
    print(formatted_rb)
    # Output: Rushing: 1,463 yards, 13 TDs, 4.8 YPC | Receiving: 45 rec, 392 yards, 2 TDs
    
    # Wide receiver stats
    wr_stats = {
        "receptions": 89,
        "receivingYards": 1364,
        "receivingTouchdowns": 11,
        "yardsPerReception": 15.3,
        "targets": 135
    }
    
    formatted_wr = format_player_stats_by_position("WR", wr_stats)
    print(formatted_wr)
    # Output: Receiving: 89 rec, 1,364 yards, 11 TDs | Avg: 15.3 yards/rec | Targets: 135


def example_structured_list():
    """Example: Formatting multiple games in a list"""
    
    games = [
        {
            "content": "Dallas Cowboys (DAL) @ Philadelphia Eagles (PHI)\n"
                      "Final: PHI 31, DAL 24 ✓\n"
                      "📍 Lincoln Financial Field"
        },
        {
            "content": "Kansas City Chiefs (KC) vs Buffalo Bills (BUF)\n"
                      "Live - 3rd Quarter, 8:42 remaining\n"
                      "Current: KC 21, BUF 17\n"
                      "📍 Arrowhead Stadium"
        }
    ]
    
    formatted_list = format_structured_list(
        games,
        title="NFL Scores - Week 18",
        separator="\n\n"
    )
    print(formatted_list)
    # Output:
    # 🏈 NFL Scores - Week 18
    #
    # Dallas Cowboys (DAL) @ Philadelphia Eagles (PHI)
    # Final: PHI 31, DAL 24 ✓
    # 📍 Lincoln Financial Field
    #
    # Kansas City Chiefs (KC) vs Buffalo Bills (BUF)
    # Live - 3rd Quarter, 8:42 remaining
    # Current: KC 21, BUF 17
    # 📍 Arrowhead Stadium


def example_complete_game_display():
    """Example: Complete game display with all formatting"""
    
    # Build a complete game display
    away = format_team_name("Dallas Cowboys", "DAL")
    home = format_team_name("Philadelphia Eagles", "PHI")
    matchup = format_matchup(away, home)
    
    game_time = format_datetime("2025-01-15T21:30Z")
    status = format_game_status("Final", 4, "0:00", True)
    score = format_score_display("DAL", 24, "PHI", 31, status, True, True)
    venue = format_venue("Lincoln Financial Field", "Philadelphia", "PA")
    network = format_broadcast_network("NBC")
    
    game_display = f"{matchup}\n{game_time}\n{score}\n{venue}\n{network}"
    print(game_display)
    # Output:
    # Dallas Cowboys (DAL) @ Philadelphia Eagles (PHI)
    # Sunday, January 15, 2025 at 4:30 PM EST
    # Final: PHI 31, DAL 24 ✓
    # 📍 Lincoln Financial Field (Philadelphia, PA)
    # 📺 NBC


if __name__ == "__main__":
    print("=== Score Formatting Examples ===")
    example_score_formatting()
    print("\n=== Schedule Formatting Examples ===")
    example_schedule_formatting()
    print("\n=== Player Stats Formatting Examples ===")
    example_player_stats_formatting()
    print("\n=== Structured List Example ===")
    example_structured_list()
    print("\n=== Complete Game Display Example ===")
    example_complete_game_display()
