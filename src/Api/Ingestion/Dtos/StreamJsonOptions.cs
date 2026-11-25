using System.Text.Json;

namespace Api.Ingestion.Dtos;

/// <summary>
/// Options System.Text.Json partagées par tout le parsing du flux du jeu.
/// </summary>
public static class StreamJsonOptions
{
    public static readonly JsonSerializerOptions Default = new JsonSerializerOptions
    {
        // Le flux envoie du PascalCase ("Event", "MatchGuid") : nos propriétés C#
        // sont en PascalCase aussi, mais on active l'insensibilité à la casse pour
        // tolérer un éventuel changement de casse côté Psyonix.
        PropertyNameCaseInsensitive = true,

        // Comportement par défaut LORSQU'ON NE PRÉCISE PAS LES OPTIONS :
        // un champ JSON sans propriété C# correspondante est IGNORÉ silencieusement.
        // C'est la "tolérance aux champs inconnus" requise par la roadmap :
        // si le jeu ajoute un champ demain, notre parser ne casse pas.
    };
}
