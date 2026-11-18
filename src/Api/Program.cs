var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();

app.MapGet("api/health", () => TypedResults.Ok(new { Status = "ok" }));

app.Run();
