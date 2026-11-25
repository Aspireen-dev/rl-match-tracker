using System.Text.Json;
using Api.Ingestion.Dtos;

namespace Api.Ingestion;

/// <summary>
/// Parseur du flux Stats API : traduit l'enveloppe {Event, Data} du jeu en événements
/// typés (DTOs). C'est la FRONTIÈRE du schéma externe (ARCHITECTURE.md) : un changement
/// de schéma côté Psyonix s'arrête ici, le reste du projet ne voit que des DTOs.
/// Conçu pour être testé unitairement avec les fixtures de captures/ (itération 5).
/// </summary>
public sealed class StreamEventParser
{
    private readonly ILogger<StreamEventParser> _logger;
    private int _updateStateCount;

    // Le tick UpdateState arrive ~30 fois/s : on ne loggue qu'un résumé tous les N.
    private const int UpdateStateLogEvery = 300;

    public StreamEventParser(ILogger<StreamEventParser> logger)
    {
        _logger = logger;
    }

    /// <summary>
    /// Parse une enveloppe et loggue un résumé de l'événement.
    /// Contrat de tolérance : ne lève JAMAIS d'exception — enveloppe null → null,
    /// payload null/vide → null silencieux, JSON invalide → warning (tronqué) + null.
    /// Dans tous les cas le flux continue.
    /// </summary>
    public ParsedStreamEvent? Parse(StreamEnvelope? envelope)
    {
        if (envelope is null)
        {
            return null;
        }

        // Dispatch par nom d'événement vers le DTO correspondant.
        // La 2e désérialisation (Data = string JSON échappée) est faite dans ParseData<T>.
        object? payload = envelope.Event switch
        {
            StreamEvents.UpdateState => ParseData<UpdateStateDto>(envelope.Data),
            StreamEvents.GoalScored => ParseData<GoalScoredDto>(envelope.Data),
            StreamEvents.StatfeedEvent => ParseData<StatfeedEventDto>(envelope.Data),
            StreamEvents.PlayerJoined or StreamEvents.PlayerLeft => ParseData<PlayerPresenceDto>(envelope.Data),
            StreamEvents.ClockUpdatedSeconds => ParseData<ClockUpdatedSecondsDto>(envelope.Data),
            StreamEvents.MatchCreated or StreamEvents.MatchInitialized or StreamEvents.MatchEnded
                or StreamEvents.MatchDestroyed or StreamEvents.MatchPaused or StreamEvents.MatchUnpaused
                or StreamEvents.RoundStarted or StreamEvents.CountdownBegin or StreamEvents.PodiumStart
                or StreamEvents.GoalReplayStart or StreamEvents.GoalReplayWillEnd or StreamEvents.GoalReplayEnd
                => ParseData<MatchEventDto>(envelope.Data),
            _ => null, // événement non mappé (BallHit, CrossbarHit...) : toléré, ignoré en V1
        };

        ParsedStreamEvent parsed = new ParsedStreamEvent(envelope.Event, payload);
        LogParsed(parsed);
        return parsed;
    }

    /// <summary>
    /// 2e désérialisation : "Data" est une string contenant du JSON échappé.
    /// Deux cas de tolérance, gérés ici :
    ///  - data null/vide  → guard clause, return null SANS warning (rien à parser) ;
    ///  - JSON invalide   → catch JsonException, warning tronqué à 200 caractères + null
    ///    (CONTRIBUTING : "log and continue on bad payloads" — le flux continue).
    /// Les champs JSON inconnus DANS le payload sont ignorés par System.Text.Json
    /// (voir StreamJsonOptions) : un champ ajouté par le jeu ne casse rien.
    /// </summary>
    private T? ParseData<T>(string? data) where T : class
    {
        // Guard clause : ne JAMAIS passer null au Deserialize (lèverait ArgumentNullException,
        // hors du catch ci-dessous, et couperait le flux). Après ce guard, data est non-null.
        if (string.IsNullOrEmpty(data))
        {
            return null;
        }

        try
        {
            return JsonSerializer.Deserialize<T>(data, StreamJsonOptions.Default);
        }
        catch (JsonException ex)
        {
            // data est non-null ici (guard ci-dessus) : on peut tronquer sans "?? \"\"".
            string preview = data.Length > 200 ? data[..200] + "..." : data;
            _logger.LogWarning(ex, "Invalid JSON for event payload: {DataPreview}", preview);
            return null;
        }
    }

    private void LogParsed(ParsedStreamEvent parsed)
    {
        switch (parsed.Event)
        {
            case StreamEvents.UpdateState when parsed.Payload is UpdateStateDto update:
                if (++_updateStateCount % UpdateStateLogEvery == 0)
                {
                    // ToString() d'un DTO n'affiche que le nom de classe : on loggue les champs utiles.
                    string score = string.Join(" - ", update.Game.Teams.Select(t => $"{t.Name} {t.Score}"));
                    _logger.LogDebug("UpdateState #{Count}: MatchGuid={MatchGuid}, Players={PlayerCount}, PlaylistId={PlaylistId}, Arena={Arena}, Score={Score}",
                        _updateStateCount, update.MatchGuid, update.Players.Count, update.Game.PlaylistId, update.Game.Arena, score);
                }
                break;

            case StreamEvents.GoalScored when parsed.Payload is GoalScoredDto goal:
                _logger.LogInformation("GoalScored: buteur={Scorer}, GoalTime={GoalTime}, vitesse={GoalSpeed}", goal.Scorer?.Name, goal.GoalTime, goal.GoalSpeed);
                break;

            case StreamEvents.StatfeedEvent when parsed.Payload is StatfeedEventDto stat:
                _logger.LogInformation("StatfeedEvent: {EventName} par {MainTarget}", stat.EventName, stat.MainTarget?.Name);
                break;

            case StreamEvents.PlayerJoined or StreamEvents.PlayerLeft when parsed.Payload is PlayerPresenceDto presence:
                _logger.LogInformation("{Event}: joueur={PlayerName}, PrimaryId={PrimaryId}", parsed.Event, presence.PlayerName, presence.PrimaryId);
                break;

            case StreamEvents.ClockUpdatedSeconds when parsed.Payload is ClockUpdatedSecondsDto clock:
                _logger.LogDebug("ClockUpdatedSeconds: TimeSeconds={Seconds}, bOvertime={Overtime}", clock.TimeSeconds, clock.bOvertime);
                break;

            case StreamEvents.MatchCreated or StreamEvents.MatchInitialized or StreamEvents.MatchEnded
                or StreamEvents.MatchDestroyed or StreamEvents.MatchPaused or StreamEvents.MatchUnpaused
                or StreamEvents.RoundStarted or StreamEvents.CountdownBegin or StreamEvents.PodiumStart
                or StreamEvents.GoalReplayStart or StreamEvents.GoalReplayWillEnd or StreamEvents.GoalReplayEnd
                when parsed.Payload is MatchEventDto matchEvent:
                _logger.LogInformation("MatchEvent: {Event}, MatchGuid={MatchGuid}, WinnerTeamNum={WinnerTeamNum}", parsed.Event, matchEvent.MatchGuid, matchEvent.WinnerTeamNum);
                break;

            default:
                _logger.LogDebug("Unknown or unparsed event: {Event}", parsed.Event);
                break;
        }
    }
}
