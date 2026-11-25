namespace Api.Ingestion.Dtos;

/// <summary>
/// Payload de l'événement "UpdateState" : le tick d'état émis ~30 fois/s.
/// Vu dans les captures réelles : Data = {"MatchGuid":..., "Players":[...], "Game":{...}}.
/// </summary>
public sealed class UpdateStateDto
{
    /// <summary>
    /// Identifiant du match en cours. Champ CONDITIONAL : null au menu / hors match online.
    /// </summary>
    public string? MatchGuid { get; set; }

    /// <summary>
    /// Joueurs présents dans le lobby (peut être vide en début de match).
    /// </summary>
    public List<PlayerDto> Players { get; set; } = [];

    /// <summary>
    /// État global de la partie (score, playlist, arène, chrono...).
    /// </summary>
    public GameDto Game { get; set; } = new();
}
