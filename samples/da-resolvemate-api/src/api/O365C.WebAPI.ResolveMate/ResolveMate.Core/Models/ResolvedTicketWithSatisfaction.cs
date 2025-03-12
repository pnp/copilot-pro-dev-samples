using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace ResolveMate.Core.Models
{
    public class ResolvedTicketWithSatisfaction
    {

        public int TicketId { get; set; }
        public int CustomerId { get; set; }
        public string? CustomerName { get; set; }
        public string? ProductName { get; set; }
        public string? TicketType { get; set; }
        public string? TicketPriority { get; set; }
        public string? TicketChannel { get; set; }
        public int CustomerSatisfactionRating { get; set; }

    }
}
