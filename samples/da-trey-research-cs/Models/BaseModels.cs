namespace TreyResearch.Models;

public class Location
{
    public string Street { get; set; } = string.Empty;
    public string City { get; set; } = string.Empty;
    public string State { get; set; } = string.Empty;
    public string Country { get; set; } = string.Empty;
    public string PostalCode { get; set; } = string.Empty;
    public double Latitude { get; set; }
    public double Longitude { get; set; }
}

public class HoursEntry
{
    public int Month { get; set; }
    public int Year { get; set; }
    public double Hours { get; set; }
}

public class Project
{
    public string Id { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;
    public string ClientName { get; set; } = string.Empty;
    public string ClientContact { get; set; } = string.Empty;
    public string ClientEmail { get; set; } = string.Empty;
    public Location Location { get; set; } = new();
    public string MapUrl { get; set; } = string.Empty;
}

public class Consultant
{
    public string Id { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public string Email { get; set; } = string.Empty;
    public string Phone { get; set; } = string.Empty;
    public string ConsultantPhotoUrl { get; set; } = string.Empty;
    public Location Location { get; set; } = new();
    public List<string> Skills { get; set; } = new();
    public List<string> Certifications { get; set; } = new();
    public List<string> Roles { get; set; } = new();
}

public class Assignment
{
    public string Id { get; set; } = string.Empty;
    public string ProjectId { get; set; } = string.Empty;
    public string ConsultantId { get; set; } = string.Empty;
    public string Role { get; set; } = string.Empty;
    public bool Billable { get; set; }
    public double Rate { get; set; }
    public List<HoursEntry> Forecast { get; set; } = new();
    public List<HoursEntry> Delivered { get; set; } = new();
}
