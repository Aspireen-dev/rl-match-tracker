namespace Api.Ingestion.Dtos;

/// <summary>
/// Payload de StatfeedEvent : {"MatchGuid":..., "EventName":"Goal"/"Shot"/"Save"/"Demolish"...,
/// "Type":..., "MainTarget":{...}, "SecondaryTarget":{...}}.
/// Source FIABLE pour compter les buts : exactement un StatfeedEvent EventName="Goal" par but
/// (contrairement à GoalScored, émis 2 fois — voir ARCHITECTURE.md).
/// </summary>
public sealed class StatfeedEventDto
{
    public string? MatchGuid { get; set; }
    public string? EventName { get; set; }
    public string? Type { get; set; }
    public PlayerRefDto? MainTarget { get; set; }
    public PlayerRefDto? SecondaryTarget { get; set; }
}
