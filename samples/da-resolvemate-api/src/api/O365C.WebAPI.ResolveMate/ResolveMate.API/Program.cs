using Microsoft.Extensions.Configuration;
using ResolveMate.Core.Interfaces;
using ResolveMate.Core.Models;
using ResolveMate.Core.Services;
using System.Runtime;
using System.Text.Json.Serialization;

var builder = WebApplication.CreateBuilder(args);


builder.Services.Configure<AppSettings>(builder.Configuration.GetSection("AppSettings"));

//Add AzureTableService as Singleton service
//builder.Services.AddSingleton<IAzureTableService, AzureTableService>();
builder.Services.AddSingleton<ISQLService, SQLService>();


builder.Services.AddControllers();
builder.Services.AddControllers().AddJsonOptions(options =>
{
    options.JsonSerializerOptions.Converters.Add(new JsonStringEnumConverter());
});
// Learn more about configuring Swagger/OpenAPI at https://aka.ms/aspnetcore/swashbuckle
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

var app = builder.Build();

// Configure the HTTP request pipeline.
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseHttpsRedirection();

app.UseAuthorization();

app.MapControllers();

app.Run();
