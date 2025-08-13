using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.Json.Serialization;
using System.Threading.Tasks;

namespace ResolveMate.Core.Models
{
    public class ResolutionMetric
    {
        public int CustomerID { get; set; }
        public required string CustomerName { get; set; }
        public int TotalTickets { get; set; }
        public int ResolvedTickets { get; set; }
        public int UnresolvedTickets { get; set; }            
        public int AvgResolutionTimeInHours { get; set; }

    }
}
