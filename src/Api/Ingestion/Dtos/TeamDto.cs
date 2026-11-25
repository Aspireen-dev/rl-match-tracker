namespace Api.Ingestion.Dtos;

/// <summary>
/// Une équipe dans Game.Teams : nom, numéro, score.
/// (Les couleurs ColorPrimary/ColorSecondary du flux sont ignorées : cosmétiques.)
/// </summary>
public sealed class TeamDto
{
    public string? Name { get; set; }
    public int TeamNum { get; set; }
    public int Score { get; set; }
}
