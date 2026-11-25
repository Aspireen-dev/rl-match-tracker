namespace Api.Ingestion.Dtos;

/// <summary>
/// Balle dans Game.Ball (vitesse, équipe qui la touche). Champs de position ignorés en V1.
/// </summary>
public sealed class BallDto
{
    public double Speed { get; set; }
    public int TeamNum { get; set; }
}
