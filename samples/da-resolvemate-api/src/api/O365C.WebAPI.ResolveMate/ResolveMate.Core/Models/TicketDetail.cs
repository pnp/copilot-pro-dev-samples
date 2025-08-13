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
    public class TicketDetail
    {
       public Ticket? Ticket { get; set; }
       public Resolution? Resolution { get; set; }
       public Customer? Customer { get; set; }

    }

}
