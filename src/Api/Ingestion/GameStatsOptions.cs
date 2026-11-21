namespace Api.Ingestion;

/// <summary>
/// Options de connexion au flux Stats API émis par Rocket League.
/// Bindées depuis la section "GameStats" de appsettings.json via <see cref="IOptions{T}"/> :
/// la configuration vit hors du code, le code reste typé et testable.
/// </summary>
public sealed class GameStatsOptions
{
    /// <summary>Nom de la section dans appsettings.json.</summary>
    public const string SectionName = "GameStats";

    /// <summary>
    /// Hôte du socket émis par le jeu. Toujours localhost : le flux est strictement
    /// local, aucune donnée ne sort de la machine du joueur.
    /// </summary>
    public string Host { get; set; } = "127.0.0.1";

    /// <summary>
    /// Port sur lequel le JEU émet son flux Stats API (49123 par défaut,
    /// cf. TAStatsAPI.ini). Notre API s'y connecte en tant que client TCP.
    /// </summary>
    public int Port { get; set; } = 49123;

    /// <summary>
    /// Délai initial de reconnexion en millisecondes après une perte de connexion
    /// (jeu non lancé, flux coupé). Il double à chaque échec (backoff exponentiel).
    /// </summary>
    public int InitialReconnectDelayMs { get; set; } = 2000;

    /// <summary>
    /// Plafond du délai de reconnexion en millisecondes : quoi qu'il arrive,
    /// on ne dépasse jamais 30 s entre deux tentatives.
    /// </summary>
    public int MaxReconnectDelayMs { get; set; } = 30000;
}
