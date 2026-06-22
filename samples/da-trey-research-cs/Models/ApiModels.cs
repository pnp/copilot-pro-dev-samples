namespace TreyResearch.Models;

public class ApiProjectAssignment
{
    public string ConsultantName { get; set; } = string.Empty;
    public Location ConsultantLocation { get; set; } = new();
    public string Role { get; set; } = string.Empty;
    public double ForecastThisMonth { get; set; }
    public double ForecastNextMonth { get; set; }
    public double DeliveredLastMonth { get; set; }
    public double DeliveredThisMonth { get; set; }
}

public class ApiProject : Project
{
    public List<ApiProjectAssignment> Consultants { get; set; } = new();
    public double ForecastThisMonth { get; set; }
    public double ForecastNextMonth { get; set; }
    public double DeliveredLastMonth { get; set; }
    public double DeliveredThisMonth { get; set; }
}

public class ApiConsultantAssignment
{
    public string ProjectName { get; set; } = string.Empty;
    public string ProjectDescription { get; set; } = string.Empty;
    public Location ProjectLocation { get; set; } = new();
    public string ClientName { get; set; } = string.Empty;
    public string ClientContact { get; set; } = string.Empty;
    public string ClientEmail { get; set; } = string.Empty;
    public string Role { get; set; } = string.Empty;
    public double ForecastThisMonth { get; set; }
    public double ForecastNextMonth { get; set; }
    public double DeliveredLastMonth { get; set; }
    public double DeliveredThisMonth { get; set; }
}

public class ApiConsultant : Consultant
{
    public List<ApiConsultantAssignment> Projects { get; set; } = new();
    public double ForecastThisMonth { get; set; }
    public double ForecastNextMonth { get; set; }
    public double DeliveredLastMonth { get; set; }
    public double DeliveredThisMonth { get; set; }
}

public class ApiChargeTimeResponse
{
    public string ClientName { get; set; } = string.Empty;
    public string ProjectName { get; set; } = string.Empty;
    public double RemainingForecast { get; set; }
    public string Message { get; set; } = string.Empty;
}

public class ApiAddConsultantToProjectResponse
{
    public string ClientName { get; set; } = string.Empty;
    public string ProjectName { get; set; } = string.Empty;
    public string ConsultantName { get; set; } = string.Empty;
    public double RemainingForecast { get; set; }
    public string Message { get; set; } = string.Empty;
}

public class ErrorResult
{
    public int Status { get; set; }
    public string Message { get; set; } = string.Empty;
}
