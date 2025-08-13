using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace ResolveMate.Core.Models
{
    public class UpdateTicketRequest
    {
        public required string TicketId { get; set; }
        public required string TicketStatus { get; set; }
        public required string TicketPriority { get; set; }
        public string ?CustomerRating { get; set; }

    }
}
