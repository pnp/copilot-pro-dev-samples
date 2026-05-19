using System.Text.Json.Serialization;

namespace TreyResearchApi.Models;

// GET requests for /projects
public class ApiProjectAssignment
{
    [JsonPropertyName("consultantName")]
    public string ConsultantName { get; set; } = "";

    [JsonPropertyName("consultantLocation")]
    public Location ConsultantLocation { get; set; } = new();

    [JsonPropertyName("role")]
    public string Role { get; set; } = "";

    [JsonPropertyName("forecastThisMonth")]
    public double ForecastThisMonth { get; set; }

    [JsonPropertyName("forecastNextMonth")]
    public double ForecastNextMonth { get; set; }

    [JsonPropertyName("deliveredLastMonth")]
    public double DeliveredLastMonth { get; set; }

    [JsonPropertyName("deliveredThisMonth")]
    public double DeliveredThisMonth { get; set; }
}

public class ApiProject : Project
{
    [JsonPropertyName("consultants")]
    public List<ApiProjectAssignment> Consultants { get; set; } = new();

    [JsonPropertyName("forecastThisMonth")]
    public double ForecastThisMonth { get; set; }

    [JsonPropertyName("forecastNextMonth")]
    public double ForecastNextMonth { get; set; }

    [JsonPropertyName("deliveredLastMonth")]
    public double DeliveredLastMonth { get; set; }

    [JsonPropertyName("deliveredThisMonth")]
    public double DeliveredThisMonth { get; set; }
}

// GET requests for /me and /consultants
public class ApiConsultantAssignment
{
    [JsonPropertyName("projectName")]
    public string ProjectName { get; set; } = "";

    [JsonPropertyName("projectDescription")]
    public string ProjectDescription { get; set; } = "";

    [JsonPropertyName("projectLocation")]
    public Location ProjectLocation { get; set; } = new();

    [JsonPropertyName("clientName")]
    public string ClientName { get; set; } = "";

    [JsonPropertyName("clientContact")]
    public string ClientContact { get; set; } = "";

    [JsonPropertyName("clientEmail")]
    public string ClientEmail { get; set; } = "";

    [JsonPropertyName("role")]
    public string Role { get; set; } = "";

    [JsonPropertyName("forecastThisMonth")]
    public double ForecastThisMonth { get; set; }

    [JsonPropertyName("forecastNextMonth")]
    public double ForecastNextMonth { get; set; }

    [JsonPropertyName("deliveredLastMonth")]
    public double DeliveredLastMonth { get; set; }

    [JsonPropertyName("deliveredThisMonth")]
    public double DeliveredThisMonth { get; set; }
}

public class ApiConsultant : Consultant
{
    [JsonPropertyName("projects")]
    public List<ApiConsultantAssignment> Projects { get; set; } = new();

    [JsonPropertyName("forecastThisMonth")]
    public double ForecastThisMonth { get; set; }

    [JsonPropertyName("forecastNextMonth")]
    public double ForecastNextMonth { get; set; }

    [JsonPropertyName("deliveredLastMonth")]
    public double DeliveredLastMonth { get; set; }

    [JsonPropertyName("deliveredThisMonth")]
    public double DeliveredThisMonth { get; set; }
}

// POST request to /api/me/chargeTime
public class ApiChargeTimeRequest
{
    [JsonPropertyName("projectName")]
    public string ProjectName { get; set; } = "";

    [JsonPropertyName("hours")]
    public double Hours { get; set; }
}

public class ApiChargeTimeResponse
{
    [JsonPropertyName("clientName")]
    public string ClientName { get; set; } = "";

    [JsonPropertyName("projectName")]
    public string ProjectName { get; set; } = "";

    [JsonPropertyName("remainingForecast")]
    public double RemainingForecast { get; set; }

    [JsonPropertyName("message")]
    public string Message { get; set; } = "";
}

// POST request to /api/projects/assignConsultant
public class ApiAddConsultantToProjectRequest
{
    [JsonPropertyName("projectName")]
    public string ProjectName { get; set; } = "";

    [JsonPropertyName("consultantName")]
    public string ConsultantName { get; set; } = "";

    [JsonPropertyName("role")]
    public string Role { get; set; } = "";

    [JsonPropertyName("forecast")]
    public double Forecast { get; set; }
}

public class ApiAddConsultantToProjectResponse
{
    [JsonPropertyName("clientName")]
    public string ClientName { get; set; } = "";

    [JsonPropertyName("projectName")]
    public string ProjectName { get; set; } = "";

    [JsonPropertyName("consultantName")]
    public string ConsultantName { get; set; } = "";

    [JsonPropertyName("remainingForecast")]
    public double RemainingForecast { get; set; }

    [JsonPropertyName("message")]
    public string Message { get; set; } = "";
}

public class ErrorResult
{
    [JsonPropertyName("status")]
    public int Status { get; set; }

    [JsonPropertyName("message")]
    public string Message { get; set; } = "";
}
