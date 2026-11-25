namespace Api.Ingestion.Dtos;

/// <summary>
/// Payload de GoalScored :
/// {"MatchGuid":..., "GoalSpeed":..., "GoalTime":..., "ImpactLocation":{"X","Y","Z"},
///  "Scorer":{"Name","Shortcut","TeamNum"}, "BallLastTouch":{"Player":{...},"Speed":...}}.
/// </summary>
/// <remarks>
/// Piège documenté (ARCHITECTURE.md) : chaque but émet GoalScored DEUX FOIS —
/// une fois avec ces données, une fois VIDE (GoalTime=0, Scorer null) pendant le
/// replay. Ne jamais compter les buts sur le nombre brut de GoalScored.
/// </remarks>
public sealed class GoalScoredDto
{
    public string? MatchGuid { get; set; }
    public double GoalSpeed { get; set; }
    public double GoalTime { get; set; }
    public Vector3Dto? ImpactLocation { get; set; }
    public PlayerRefDto? Scorer { get; set; }

    /// <summary>
    /// Passeur décisif. Champ CONDITIONAL (absent si but sans passe) — doc officielle.
    /// </summary>
    public PlayerRefDto? Assister { get; set; }

    public BallLastTouchDto? BallLastTouch { get; set; }
}

public sealed class Vector3Dto
{
    public double X { get; set; }
    public double Y { get; set; }
    public double Z { get; set; }
}

public sealed class BallLastTouchDto
{
    public PlayerRefDto? Player { get; set; }
    public double Speed { get; set; }
}
