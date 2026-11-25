namespace Api.Ingestion.Dtos;

/// <summary>
/// Événements de match qui ne portent qu'un MatchGuid :
/// MatchCreated, MatchInitialized, MatchEnded (aussi WinnerTeamNum), PodiumStart,
/// RoundStarted, CountdownBegin, GoalReplayStart/WillEnd/End, MatchPaused/Unpaused...
/// </summary>
public sealed class MatchEventDto
{
    /// <summary>
    /// Champ CONDITIONAL : présent en match online, peut manquer ailleurs.
    /// </summary>
    public string? MatchGuid { get; set; }

    /// <summary>
    /// Valorisé uniquement par MatchEnded (0 ou 1).
    /// </summary>
    public int? WinnerTeamNum { get; set; }
}
