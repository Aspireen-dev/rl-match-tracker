using Api.Ingestion;

WebApplicationBuilder builder = WebApplication.CreateBuilder(args);

builder.Services.Configure<GameStatsOptions>(builder.Configuration.GetSection(GameStatsOptions.SectionName));
// Parseur du flux (singleton : une seule connexion au jeu à la fois, il garde un compteur de ticks).
builder.Services.AddSingleton<StreamEventParser>();
builder.Services.AddHostedService<GameStatsIngestionService>();

WebApplication app = builder.Build();

app.MapGet("api/health", () => TypedResults.Ok(new { Status = "ok" }));

app.Run();
