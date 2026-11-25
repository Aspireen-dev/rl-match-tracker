namespace Api.Ingestion.Dtos;

/// <summary>
/// Enveloppe de CHAQUE message du flux Stats API :
/// <code>{"Event":"UpdateState","Data":"&lt;json échappé dans une string&gt;"}</code>
/// </summary>
/// <remarks>
/// "Data" est une string qui contient du JSON sérialisé (avec ses " échappés) :
/// il faudra une DEUXIÈME désérialisation pour obtenir le vrai contenu typé.
/// C'est la "double désérialisation" notée dans le journal (session 2026-11-21).
///
/// Divergence doc vs réalité : la doc officielle montre "Data" comme un objet JSON,
/// mais le wire format réel (confirmé sur nos captures) envoie Data EN STRING échappée.
/// </remarks>
public sealed class StreamEnvelope
{
    /// <summary>
    /// Nom de l'événement ("UpdateState", "GoalScored", "MatchCreated"...).
    /// </summary>
    public string Event { get; set; } = "";

    /// <summary>
    /// Payload JSON sérialisé DANS une string (à re-parser selon Event).
    /// </summary>
    public string Data { get; set; } = "";
}
