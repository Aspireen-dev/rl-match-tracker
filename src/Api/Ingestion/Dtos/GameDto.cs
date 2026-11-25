namespace Api.Ingestion.Dtos;

/// <summary>
/// Bloc "Game" d'un UpdateState : état global de la partie.
/// Les champs cosmétiques ou sans intérêt V1 (couleurs d'équipe...) ne sont PAS
/// déclarés : System.Text.Json les ignore automatiquement (tolérance).
/// </summary>
public sealed class GameDto
{
    public List<TeamDto> Teams { get; set; } = [];

    /// <summary>
    /// ID numérique de la playlist (vu: 2 pour un 2v2). À corréler avec les modes de jeu.
    /// </summary>
    public int? PlaylistId { get; set; }

    /// <summary>
    /// Nom de l'arène (ex. "NeoTokyo_Arcade_P").
    /// </summary>
    public string? Arena { get; set; }

    /// <summary>
    /// Temps restant en secondes.
    /// </summary>
    public double TimeSeconds { get; set; }

    public bool bOvertime { get; set; }
    public bool bReplay { get; set; }
    public bool bHasWinner { get; set; }
    public string? Winner { get; set; }
    public bool bHasTarget { get; set; }

    public BallDto? Ball { get; set; }
}
