using Weather.Places;
var builder = WebApplication.CreateBuilder(args);
builder.Services.AddControllers();
builder.Services.AddSingleton<PlacesRepository>();
builder.Services.AddHostedService<RequestPublisher>();
var app = builder.Build();
app.MapControllers();
app.Run();
