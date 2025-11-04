"""
NFL Data Formatting Utilities
Provides consistent formatting functions for NFL data across all agents
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
import pytz


def format_datetime(
    iso_datetime: str,
    timezone: str = "US/Eastern",
    include_day: bool = True
) -> str:
    """
    Format ISO datetime to user-friendly format.
    
    Args:
        iso_datetime: ISO format datetime string (e.g., "2025-01-15T21:30Z")
        timezone: Target timezone (default: US/Eastern)
        include_day: Whether to include day of week
    
    Returns:
        Formatted string like "Sunday, January 15, 2025 at 4:30 PM EST"
    
    Examples:
        >>> format_datetime("2025-01-15T21:30Z")
        "Sunday, January 15, 2025 at 4:30 PM EST"
        >>> format_datetime("2025-01-15T21:30Z", include_day=False)
        "January 15, 2025 at 4:30 PM EST"
    """
    try:
        # Parse ISO datetime
        dt = datetime.fromisoformat(iso_datetime.replace('Z', '+00:00'))
        
        # Convert to target timezone
        tz = pytz.timezone(timezone)
        dt_local = dt.astimezone(tz)
        
        # Format components
        if include_day:
            day_name = dt_local.strftime("%A")
            date_str = dt_local.strftime("%B %d, %Y")
            time_str = dt_local.strftime("%I:%M %p").lstrip('0')
            tz_abbr = dt_local.strftime("%Z")
            return f"{day_name}, {date_str} at {time_str} {tz_abbr}"
        else:
            date_str = dt_local.strftime("%B %d, %Y")
            time_str = dt_local.strftime("%I:%M %p").lstrip('0')
            tz_abbr = dt_local.strftime("%Z")
            return f"{date_str} at {time_str} {tz_abbr}"
    except Exception as e:
        # Fallback to original string if parsing fails
        return iso_datetime


def format_team_name(
    full_name: str,
    abbreviation: str,
    include_abbr: bool = True
) -> str:
    """
    Format team name with full name and abbreviation.
    
    Args:
        full_name: Full team name (e.g., "Dallas Cowboys")
        abbreviation: Team abbreviation (e.g., "DAL")
        include_abbr: Whether to include abbreviation in parentheses
    
    Returns:
        Formatted string like "Dallas Cowboys (DAL)"
    
    Examples:
        >>> format_team_name("Dallas Cowboys", "DAL")
        "Dallas Cowboys (DAL)"
        >>> format_team_name("Dallas Cowboys", "DAL", include_abbr=False)
        "Dallas Cowboys"
    """
    if include_abbr and abbreviation:
        return f"{full_name} ({abbreviation})"
    return full_name


def format_score_display(
    away_team: str,
    away_score: int,
    home_team: str,
    home_score: int,
    status: str,
    is_completed: bool = False,
    highlight_winner: bool = True
) -> str:
    """
    Format score display with optional winner highlighting.
    
    Args:
        away_team: Away team name (formatted)
        away_score: Away team score
        home_team: Home team name (formatted)
        home_score: Home team score
        status: Game status (e.g., "Final", "3rd Quarter")
        is_completed: Whether game is completed
        highlight_winner: Whether to highlight winning team
    
    Returns:
        Formatted score string
    
    Examples:
        >>> format_score_display("DAL", 24, "PHI", 31, "Final", True)
        "Final: PHI 31, DAL 24 ✓"
    """
    if is_completed and highlight_winner:
        if home_score > away_score:
            return f"{status}: {home_team} {home_score}, {away_team} {away_score} ✓"
        elif away_score > home_score:
            return f"{status}: {away_team} {away_score}, {home_team} {home_score} ✓"
        else:
            return f"{status}: {away_team} {away_score}, {home_team} {home_score} (Tie)"
    else:
        return f"{status}: {away_team} {away_score}, {home_team} {home_score}"


def format_game_status(
    status_type: str,
    period: int = 0,
    clock: str = "",
    is_completed: bool = False
) -> str:
    """
    Format game status for live and completed games.
    
    Args:
        status_type: Status description (e.g., "Final", "In Progress")
        period: Current period/quarter
        clock: Time remaining
        is_completed: Whether game is completed
    
    Returns:
        Formatted status string
    
    Examples:
        >>> format_game_status("In Progress", 3, "8:42")
        "Live - 3rd Quarter, 8:42 remaining"
        >>> format_game_status("Final", 4, "0:00", True)
        "Final"
    """
    if is_completed:
        return "Final"
    
    # Map period numbers to quarter names
    quarter_names = {
        1: "1st Quarter",
        2: "2nd Quarter",
        3: "3rd Quarter",
        4: "4th Quarter",
        5: "Overtime"
    }
    
    if period in quarter_names:
        quarter = quarter_names[period]
        if clock and clock != "0:00":
            return f"Live - {quarter}, {clock} remaining"
        else:
            return f"Live - {quarter}"
    
    return status_type


def format_structured_list(
    items: List[Dict[str, Any]],
    title: str = "",
    separator: str = "\n\n"
) -> str:
    """
    Format multiple items into a structured list.
    
    Args:
        items: List of dictionaries with 'content' key
        title: Optional title for the list
        separator: Separator between items
    
    Returns:
        Formatted list string
    
    Examples:
        >>> items = [{"content": "Game 1"}, {"content": "Game 2"}]
        >>> format_structured_list(items, "NFL Games")
        "🏈 NFL Games\\n\\nGame 1\\n\\nGame 2"
    """
    result = []
    
    if title:
        result.append(f"🏈 {title}")
        result.append("")
    
    for item in items:
        if isinstance(item, dict) and 'content' in item:
            result.append(item['content'])
        elif isinstance(item, str):
            result.append(item)
    
    return separator.join(result)


def format_player_stats_by_position(
    position: str,
    stats: Dict[str, Any]
) -> str:
    """
    Format player statistics based on their position.
    
    Args:
        position: Player position (QB, RB, WR, TE, K, P, DEF)
        stats: Dictionary of statistics
    
    Returns:
        Formatted statistics string
    
    Examples:
        >>> stats = {"passingYards": 4183, "passingTouchdowns": 32}
        >>> format_player_stats_by_position("QB", stats)
        "Passing: 4,183 yards, 32 TDs"
    """
    position = position.upper()
    formatted_stats = []
    
    if position == "QB":
        # Quarterback stats
        if "passingYards" in stats:
            yards = f"{stats['passingYards']:,}"
            tds = stats.get('passingTouchdowns', 0)
            ints = stats.get('interceptions', 0)
            formatted_stats.append(f"Passing: {yards} yards, {tds} TDs, {ints} INTs")
        
        if "completionPct" in stats:
            pct = stats['completionPct']
            formatted_stats.append(f"Completion: {pct}%")
        
        if "qbRating" in stats:
            rating = stats['qbRating']
            formatted_stats.append(f"QB Rating: {rating}")
        
        if "rushingYards" in stats and stats['rushingYards'] > 0:
            yards = stats['rushingYards']
            tds = stats.get('rushingTouchdowns', 0)
            formatted_stats.append(f"Rushing: {yards} yards, {tds} TDs")
    
    elif position in ["RB", "FB"]:
        # Running back stats
        if "rushingYards" in stats:
            yards = f"{stats['rushingYards']:,}"
            tds = stats.get('rushingTouchdowns', 0)
            ypc = stats.get('yardsPerCarry', 0)
            formatted_stats.append(f"Rushing: {yards} yards, {tds} TDs, {ypc} YPC")
        
        if "receptions" in stats:
            rec = stats['receptions']
            yards = stats.get('receivingYards', 0)
            tds = stats.get('receivingTouchdowns', 0)
            formatted_stats.append(f"Receiving: {rec} rec, {yards} yards, {tds} TDs")
    
    elif position in ["WR", "TE"]:
        # Receiver stats
        if "receptions" in stats:
            rec = stats['receptions']
            yards = f"{stats.get('receivingYards', 0):,}"
            tds = stats.get('receivingTouchdowns', 0)
            formatted_stats.append(f"Receiving: {rec} rec, {yards} yards, {tds} TDs")
        
        if "yardsPerReception" in stats:
            ypr = stats['yardsPerReception']
            formatted_stats.append(f"Avg: {ypr} yards/rec")
        
        if "targets" in stats:
            targets = stats['targets']
            formatted_stats.append(f"Targets: {targets}")
    
    elif position == "K":
        # Kicker stats
        if "fieldGoalsMade" in stats:
            made = stats['fieldGoalsMade']
            att = stats.get('fieldGoalsAttempted', made)
            pct = (made / att * 100) if att > 0 else 0
            formatted_stats.append(f"Field Goals: {made}/{att} ({pct:.1f}%)")
        
        if "extraPointsMade" in stats:
            xp = stats['extraPointsMade']
            formatted_stats.append(f"Extra Points: {xp}")
        
        if "longestFieldGoal" in stats:
            longest = stats['longestFieldGoal']
            formatted_stats.append(f"Long: {longest} yards")
    
    elif position == "P":
        # Punter stats
        if "punts" in stats:
            punts = stats['punts']
            yards = stats.get('puntYards', 0)
            avg = stats.get('puntAverage', 0)
            formatted_stats.append(f"Punts: {punts} for {yards} yards ({avg} avg)")
        
        if "longestPunt" in stats:
            longest = stats['longestPunt']
            formatted_stats.append(f"Long: {longest} yards")
    
    else:
        # Defensive stats
        if "tackles" in stats:
            tackles = stats['tackles']
            formatted_stats.append(f"Tackles: {tackles}")
        
        if "sacks" in stats:
            sacks = stats['sacks']
            formatted_stats.append(f"Sacks: {sacks}")
        
        if "interceptions" in stats:
            ints = stats['interceptions']
            formatted_stats.append(f"Interceptions: {ints}")
        
        if "forcedFumbles" in stats:
            ff = stats['forcedFumbles']
            formatted_stats.append(f"Forced Fumbles: {ff}")
    
    return " | ".join(formatted_stats) if formatted_stats else "No statistics available"


def format_venue(venue_name: str, city: str = "", state: str = "") -> str:
    """
    Format venue information with location.
    
    Args:
        venue_name: Stadium/venue name
        city: City name (optional)
        state: State abbreviation (optional)
    
    Returns:
        Formatted venue string
    
    Examples:
        >>> format_venue("AT&T Stadium", "Arlington", "TX")
        "📍 AT&T Stadium (Arlington, TX)"
        >>> format_venue("AT&T Stadium")
        "📍 AT&T Stadium"
    """
    if city and state:
        return f"📍 {venue_name} ({city}, {state})"
    elif city:
        return f"📍 {venue_name} ({city})"
    else:
        return f"📍 {venue_name}"


def format_broadcast_network(network: str) -> str:
    """
    Format broadcast network information.
    
    Args:
        network: Network name (e.g., "NBC", "ESPN")
    
    Returns:
        Formatted network string
    
    Examples:
        >>> format_broadcast_network("NBC")
        "📺 NBC"
    """
    if network:
        return f"📺 {network}"
    return ""


def format_matchup(
    away_team: str,
    home_team: str,
    is_neutral: bool = False
) -> str:
    """
    Format team matchup display.
    
    Args:
        away_team: Away team name (formatted)
        home_team: Home team name (formatted)
        is_neutral: Whether it's a neutral site game
    
    Returns:
        Formatted matchup string
    
    Examples:
        >>> format_matchup("Dallas Cowboys (DAL)", "Philadelphia Eagles (PHI)")
        "Dallas Cowboys (DAL) @ Philadelphia Eagles (PHI)"
        >>> format_matchup("Team A", "Team B", is_neutral=True)
        "Team A vs Team B"
    """
    if is_neutral:
        return f"{away_team} vs {home_team}"
    else:
        return f"{away_team} @ {home_team}"
