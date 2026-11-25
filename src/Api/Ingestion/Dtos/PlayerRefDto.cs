namespace Api.Ingestion.Dtos;

/// <summary>
/// Référence légère à un joueur dans les événements (Scorer, MainTarget...) :
/// seulement Name / Shortcut / TeamNum (pas de PrimaryId dans ces blocs).
/// </summary>
public sealed class PlayerRefDto
{
    public string? Name { get; set; }
    public int Shortcut { get; set; }
    public int TeamNum { get; set; }
}
