using System;

namespace ResolveMate.Core.Models
{
    public class Product
    {
        public int ProductID { get; set; }
        public string ProductName { get; set; }
        public string ProductCategory { get; set; }
        public DateTime? PurchasedDate { get; set; }
    }
}