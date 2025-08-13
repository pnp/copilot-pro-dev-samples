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
    public class Ticket
    {
        
        
        public int CustomerID { get; set; }
        public string? CustomerName { get; set; }
        public string? CustomerEmail { get; set; }
        public int TicketID { get; set; }
        public string TicketType { get; set; }
        public string TicketSubject { get; set; }
        public string TicketDescription { get; set; }
        public string TicketStatus { get; set; }
        public string TicketPriority { get; set; }
        public string TicketChannel { get; set; }
        public DateTime? FirstResponseTime { get; set; }
        public DateTime? TimeToResolution { get; set; }
        public float CustomerSatisfactionRating { get; set; }
        public int? ProductID { get; set; }
        public string ?ProductName { get; set; }
        public string ?ProductCategory { get; set; }
        public DateTime? PurchasedDate { get; set; }
        public string? Resolution { get; set; }
        public DateTime? ResolutionDate { get; set; }

    }

}

