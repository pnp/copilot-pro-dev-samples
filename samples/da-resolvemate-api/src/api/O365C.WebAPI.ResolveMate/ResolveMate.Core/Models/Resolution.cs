using System;

namespace ResolveMate.Core.Models
{
    public class Resolution
    {
        public int ResolutionID { get; set; }
        public int TicketID { get; set; }
        public string ResolutionText { get; set; }
        public DateTime? ResolutionDate { get; set; }
    }
}