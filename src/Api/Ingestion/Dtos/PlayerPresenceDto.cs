namespace Api.Ingestion.Dtos;

/// <summary>
/// Payload de PlayerJoined / PlayerLeft :
/// {"MatchGuid":..., "PlayerName":"...", "PrimaryId":"Steam|...|0"}.
/// </summary>
public sealed class PlayerPresenceDto
{
    public string? MatchGuid { get; set; }
    public string? PlayerName { get; set; }

    /// <summary>
    /// Format "Platform|Uid|Splitscreen" — sert à identifier le joueur local configuré.
    /// </summary>
    public string? PrimaryId { get; set; }
}
