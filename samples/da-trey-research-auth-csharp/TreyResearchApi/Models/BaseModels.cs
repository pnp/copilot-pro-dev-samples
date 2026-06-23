using System.Text.Json.Serialization;

namespace TreyResearchApi.Models;

public class Location
{
    [JsonPropertyName("street")]
    public string Street { get; set; } = "";

    [JsonPropertyName("city")]
    public string City { get; set; } = "";

    [JsonPropertyName("state")]
    public string State { get; set; } = "";

    [JsonPropertyName("country")]
    public string Country { get; set; } = "";

    [JsonPropertyName("postalCode")]
    public string PostalCode { get; set; } = "";

    [JsonPropertyName("latitude")]
    public double Latitude { get; set; }

    [JsonPropertyName("longitude")]
    public double Longitude { get; set; }
}

public class HoursEntry
{
    [JsonPropertyName("month")]
    public int Month { get; set; }

    [JsonPropertyName("year")]
    public int Year { get; set; }

    [JsonPropertyName("hours")]
    public double Hours { get; set; }
}

public class Project
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = "";

    [JsonPropertyName("name")]
    public string Name { get; set; } = "";

    [JsonPropertyName("description")]
    public string Description { get; set; } = "";

    [JsonPropertyName("clientName")]
    public string ClientName { get; set; } = "";

    [JsonPropertyName("clientContact")]
    public string ClientContact { get; set; } = "";

    [JsonPropertyName("clientEmail")]
    public string ClientEmail { get; set; } = "";

    [JsonPropertyName("location")]
    public Location Location { get; set; } = new();

    [JsonPropertyName("mapUrl")]
    public string MapUrl { get; set; } = "";
}

public class Consultant
{
    [JsonPropertyName("id")]
    public string? Id { get; set; }

    [JsonPropertyName("name")]
    public string Name { get; set; } = "";

    [JsonPropertyName("email")]
    public string Email { get; set; } = "";

    [JsonPropertyName("phone")]
    public string Phone { get; set; } = "";

    [JsonPropertyName("consultantPhotoUrl")]
    public string ConsultantPhotoUrl { get; set; } = "";

    [JsonPropertyName("location")]
    public Location Location { get; set; } = new();

    [JsonPropertyName("skills")]
    public List<string> Skills { get; set; } = new();

    [JsonPropertyName("certifications")]
    public List<string> Certifications { get; set; } = new();

    [JsonPropertyName("roles")]
    public List<string> Roles { get; set; } = new();
}

public class Assignment
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = "";

    [JsonPropertyName("projectId")]
    public string ProjectId { get; set; } = "";

    [JsonPropertyName("consultantId")]
    public string ConsultantId { get; set; } = "";

    [JsonPropertyName("role")]
    public string Role { get; set; } = "";

    [JsonPropertyName("billable")]
    public bool Billable { get; set; }

    [JsonPropertyName("rate")]
    public double Rate { get; set; }

    [JsonPropertyName("forecast")]
    public List<HoursEntry> Forecast { get; set; } = new();

    [JsonPropertyName("delivered")]
    public List<HoursEntry> Delivered { get; set; } = new();
}
