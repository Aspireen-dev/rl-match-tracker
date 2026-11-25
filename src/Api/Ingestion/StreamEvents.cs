namespace Api.Ingestion;

/// <summary>
/// Noms des événements émis par le flux Stats API, en constantes :
/// évite les fautes de frappe dans les switch et rend la recherche
/// globale possible dans tout le projet.
/// Source : doc officielle + captures réelles (captures/*.jsonl).
/// </summary>
public static class StreamEvents
{
    // Tick d'état (~30/s selon PacketSendRate)
    public const string UpdateState = "UpdateState";
    public const string ClockUpdatedSeconds = "ClockUpdatedSeconds";

    // Événements de jeu
    public const string BallHit = "BallHit";
    public const string CrossbarHit = "CrossbarHit";
    public const string GoalScored = "GoalScored";
    public const string StatfeedEvent = "StatfeedEvent";

    // Présence des joueurs
    public const string PlayerJoined = "PlayerJoined";
    public const string PlayerLeft = "PlayerLeft";

    // Cycle de vie du match et des rounds/replays
    public const string MatchCreated = "MatchCreated";
    public const string MatchInitialized = "MatchInitialized";
    public const string MatchEnded = "MatchEnded";
    public const string MatchDestroyed = "MatchDestroyed";
    public const string MatchPaused = "MatchPaused";
    public const string MatchUnpaused = "MatchUnpaused";
    public const string RoundStarted = "RoundStarted";
    public const string CountdownBegin = "CountdownBegin";
    public const string PodiumStart = "PodiumStart";
    public const string GoalReplayStart = "GoalReplayStart";
    public const string GoalReplayWillEnd = "GoalReplayWillEnd";
    public const string GoalReplayEnd = "GoalReplayEnd";
}
