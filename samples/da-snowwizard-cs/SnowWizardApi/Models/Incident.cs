namespace SnowWizardApi.Models;

public class Incident
{
    public string Number { get; set; } = "";
    public string Name { get; set; } = "";
    public string Description { get; set; } = "";
    public string ClientName { get; set; } = "";
    public string ClientContact { get; set; } = "";
    public string ClientEmail { get; set; } = "";
    public string MapUrl { get; set; } = "";
}
