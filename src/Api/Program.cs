using Api.Ingestion;

WebApplicationBuilder builder = WebApplication.CreateBuilder(args);

builder.Services.Configure<GameStatsOptions>(builder.Configuration.GetSection(GameStatsOptions.SectionName));
builder.Services.AddHostedService<GameStatsIngestionService>();

WebApplication app = builder.Build();

app.MapGet("api/health", () => TypedResults.Ok(new { Status = "ok" }));

app.Run();
