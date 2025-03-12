namespace M365.Comms.API.Models
{
    /// <summary>
    /// Represents the settings for the Azure AD configuration.
    /// </summary>
    public class AzureADSettings
    {
        /// <summary>
        /// Gets or sets the "Application (client) ID" of the app registration in Azure.
        /// </summary>
        public string? ClientId { get; set; }

        /// <summary>
        /// Gets or sets the client secret of the app registration in Azure.
        /// </summary>
        public string? ClientSecret { get; set; }

        /// <summary>
        /// Gets or sets the "Directory (tenant) ID" of the app registration in Azure.
        /// </summary>
        public string? TenantId { get; set; }

        /// <summary>
        /// Gets or sets the Azure AD instance.
        /// </summary>
        public string? Instance { get; set; }
    }
}
