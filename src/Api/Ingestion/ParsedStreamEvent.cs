namespace Api.Ingestion;

/// <summary>
/// Résultat du parsing d'une enveloppe du flux : le nom de l'événement
/// + le payload désérialisé dans son DTO (null si événement non mappé ou payload illisible).
/// </summary>
public sealed record ParsedStreamEvent(string Event, object? Payload);
