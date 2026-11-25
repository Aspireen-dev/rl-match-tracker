namespace Api.Ingestion.Dtos;

/// <summary>
/// Un joueur dans UpdateState.Players[].
/// Vu dans les captures : compteurs CUMULATIFS (Score, Goals, Shots, Assists, Saves,
/// Demos...) dont la dernière valeur du match = le total, et champs instantanés
/// (Boost, Speed, bOnGround) qui changent à chaque tick.
/// </summary>
public sealed class PlayerDto
{
    public string? Name { get; set; }

    /// <summary>
    /// Identifiant stable du joueur, format "Platform|Uid|Splitscreen" (ex. "Steam|76561198149344717|0").
    /// </summary>
    public string? PrimaryId { get; set; }

    public int Shortcut { get; set; }
    public int TeamNum { get; set; }

    // --- compteurs cumulatifs sur le match ---
    public int Score { get; set; }
    public int Goals { get; set; }
    public int Shots { get; set; }
    public int Assists { get; set; }
    public int Saves { get; set; }
    public int Touches { get; set; }
    public int CarTouches { get; set; }
    public int Demos { get; set; }

    // --- état instantané (change à chaque tick, à ne PAS persister tel quel) ---
    public int? Boost { get; set; }
    public double? Speed { get; set; }
    public bool bOnGround { get; set; }
    public bool bHasCar { get; set; }

    // Loadout (cosmétique) volontairement non déclaré : ignoré par le serializer.
}
