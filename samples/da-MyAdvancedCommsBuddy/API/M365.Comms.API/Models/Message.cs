using System.Collections.Generic;
using System.ComponentModel;
using System.Text.Json.Serialization;

namespace M365.Comms.API.Models
{
    /// <summary>
    /// Represents a message that can be sent to Microsoft 365 services.
    /// </summary>
    public class Message
    {
        /// <summary>
        /// Initializes a new instance of the <see cref="Message"/> class.
        /// </summary>
        public Message()
        {
            // Set default values.
            Approval = ApprovalStatus.Pending;
            MarkdownContent = string.Empty;
            ReviewItemUrl = string.Empty;
        }

        /// <summary>
        /// Gets or sets the unique identifier of the message.
        /// </summary>
        public int Id { get; set; }

        /// <summary>
        /// Gets or sets the title of the message.
        /// </summary>
        public string MarkdownContent { get; set; }

        /// <summary>
        /// Gets or sets the approval status of the message.
        /// </summary>
        public ApprovalStatus Approval { get; set; }
               
        /// <summary>
        /// Gets or sets a value indicating whether the message should be sent to SharePoint.
        /// </summary>
        public bool SendToSharePoint { get; set; }

        /// <summary>
        /// Gets or sets a value indicating whether the message should be sent to Teams.
        /// </summary>
        public bool SendToTeams { get; set; }

        /// <summary>
        /// Gets or sets a value indicating whether the message should be sent to Outlook.
        /// </summary>
        public bool SendToOutlook { get; set; }

        /// <summary>
        /// Gets or sets the URL of the item to be reviewed.
        /// </summary>
        public string ReviewItemUrl { get; set; }
    }

    
    public enum ApprovalStatus
    {
        Pending,
        Approved,
        Rejected,
        Cancelled,
        Submitted
    }
}
