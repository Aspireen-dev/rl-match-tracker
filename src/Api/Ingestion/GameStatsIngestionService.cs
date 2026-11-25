using System.Net.Sockets;
using System.Text.Json;
using Api.Ingestion.Dtos;
using Microsoft.Extensions.Options;

namespace Api.Ingestion;

// Service d'arrière-plan qui maintient une connexion TCP au flux Stats API du jeu.
// Le JEU fait office de serveur (localhost:49123) : notre API est le client.
// Responsabilité ici : UNIQUEMENT le transport (connexion, boucle de lecture, reconnexion).
// Le parsing typé est délégué au StreamEventParser.
public sealed class GameStatsIngestionService : BackgroundService
{
    private readonly ILogger<GameStatsIngestionService> _logger;
    private readonly GameStatsOptions _options;
    private readonly StreamEventParser _parser;

    // DI : le conteneur ASP.NET Core injecte le logger, les options et le parser tout seuls.
    public GameStatsIngestionService(ILogger<GameStatsIngestionService> logger, IOptions<GameStatsOptions> options, StreamEventParser parser)
    {
        _logger = logger;
        _options = options.Value; // .Value = l'objet rempli depuis appsettings.json
        _parser = parser;
    }

    // Boucle principale : tourne jusqu'à l'arrêt de l'app et se reconnecte à chaque perte de flux.
    protected override async Task ExecuteAsync(CancellationToken cancellationToken)
    {
        int delayMs = _options.InitialReconnectDelayMs;

        while (!cancellationToken.IsCancellationRequested)
        {
            try
            {
                await ConnectAndReadAsync(cancellationToken);
                // La connexion a tenu et le flux s'est terminé proprement : on repart du délai initial.
                delayMs = _options.InitialReconnectDelayMs;
            }
            catch (OperationCanceledException) when (cancellationToken.IsCancellationRequested)
            {
                // Arrêt demandé (shutdown de l'app) : on sort sans erreur.
                _logger.LogInformation("GameStatsIngestionService is stopping.");
                break;
            }
            catch (Exception ex) when (ex is SocketException or IOException)
            {
                // Jeu non lancé ou flux coupé brutalement : on attend avant de retenter,
                // le délai double à chaque échec (backoff exponentiel, plafonné à MaxReconnectDelayMs).
                _logger.LogWarning(ex, "Could not reach the game at {Host}:{Port}, retry in {DelayMs} ms", _options.Host, _options.Port, delayMs);
                await Task.Delay(delayMs, cancellationToken);
                delayMs = Math.Min(delayMs * 2, _options.MaxReconnectDelayMs);
            }
        }
    }

    private async Task ConnectAndReadAsync(CancellationToken cancellationToken)
    {
        // using TcpClient = la socket est libérée quoi qu'il arrive (return, exception...).
        using TcpClient client = new TcpClient();
        await client.ConnectAsync(_options.Host, _options.Port, cancellationToken);
        _logger.LogInformation("Connected to the game at {Host}:{Port}, reading the stream...", _options.Host, _options.Port);

        using NetworkStream stream = client.GetStream();

        try
        {
            // Le flux est un stream d'objets JSON concaténés (aucun séparateur) :
            // topLevelValues: true (.NET 9+) lit les valeurs top-level successives directement (~30/s).
            await foreach (StreamEnvelope? envelope in JsonSerializer.DeserializeAsyncEnumerable<StreamEnvelope>(stream, topLevelValues: true, cancellationToken: cancellationToken))
            {
                // Parsing délégué : double désérialisation + dispatch vers les DTOs.
                // Un payload illisible ne lève pas ici (géré dans le parser) et ne coupe pas la connexion.
                _parser.Parse(envelope);
            }
        }
        catch (JsonException ex)
        {
            // Flux coupé en plein JSON : on logue et on laisse ExecuteAsync reconnecter.
            _logger.LogWarning(ex, "Fin de flux sur JsonException: {Error}", ex.Message);
        }
    }
}
