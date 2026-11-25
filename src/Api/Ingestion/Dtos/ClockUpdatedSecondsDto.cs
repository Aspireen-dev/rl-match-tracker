namespace Api.Ingestion.Dtos;

/// <summary>
/// Payload de ClockUpdatedSeconds : {"MatchGuid":..., "TimeSeconds":..., "bOvertime":...}.
/// </summary>
public sealed class ClockUpdatedSecondsDto
{
    public string? MatchGuid { get; set; }
    public double TimeSeconds { get; set; }
    public bool bOvertime { get; set; }
}
