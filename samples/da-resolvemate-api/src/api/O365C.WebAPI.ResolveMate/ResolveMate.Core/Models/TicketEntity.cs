using Azure;
using Azure.Data.Tables;
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.ComponentModel.DataAnnotations;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
namespace ResolveMate.Core.Models
{
    public class TicketEntity : ITableEntity
    {
        public string PartitionKey { get; set; }
        public string RowKey { get; set; }        
        public DateTimeOffset? Timestamp { get; set; }
        public string TicketId { get; set; }
        public string CustomerName { get; set; }
        public string CustomerEmail { get; set; }
        public int CustomerAge { get; set; }
        public string CustomerGender { get; set; }
        public string ProductPurchased { get; set; }
        public DateTimeOffset DateOfPurchase { get; set; }
        public string TicketType { get; set; }
        public string TicketSubject { get; set; }
        public string TicketDescription { get; set; }
        public string TicketStatus { get; set; }
        public string Resolution { get; set; }
        public string TicketPriority { get; set; }
        public string TicketChannel { get; set; }
        public DateTimeOffset? FirstResponseTime { get; set; }
        public DateTimeOffset? TimeToResolution { get; set; }
        public int CustomerSatisfactionRating { get; set; }

        public ETag ETag { get; set; }
    }

    public enum TicketPriority
    {
        Critical,
        Low,
        High,
        Medium
    }
    public enum TicketType
    {
        [Display(Name= "Technical issue,")]
        TechnicalIssue,
        [Display(Name = "Billing issue,")]
        BillingIssue,
        [Display(Name = " Cancellation request,")]
        CancellationRequest,
        [Display(Name = "Product inquiry")]
        ProductInquiry,
        [Display(Name = "Refund request")]
        RefundRequest

    }

  
}

