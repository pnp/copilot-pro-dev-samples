using Azure;
using Azure.Data.Tables;
using ResolveMate.Core.Models;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace ResolveMate.Core.Mappers
{
    
        public static class TicketMapper
        {
            public static TicketEntity MapEntityToTicketAsync(TableEntity entity)
            {
                if (entity == null)
                {
                    throw new ArgumentNullException(nameof(entity), "TableEntity cannot be null");
                }

                var ticket = new TicketEntity
                {
                    PartitionKey = entity.PartitionKey,
                    RowKey = entity.RowKey,
                    ETag = entity.ETag,
                    Timestamp = entity.Timestamp,
                    TicketId = entity.GetString("TicketId"),
                    CustomerName = entity.GetString("CustomerName"),
                    CustomerEmail = entity.GetString("CustomerEmail"),
                    CustomerAge = entity.GetInt32("CustomerAge") ?? 0,
                    CustomerGender = entity.GetString("CustomerGender"),
                    ProductPurchased = entity.GetString("ProductPurchased"),
                    DateOfPurchase = entity.GetDateTimeOffset("DateOfPurchase") ?? DateTimeOffset.MinValue,
                    TicketType = entity.GetString("string"),
                    TicketSubject = entity.GetString("TicketSubject"),
                    TicketDescription = entity.GetString("TicketDescription"),
                    TicketStatus = entity.GetString("TicketStatus"),
                    Resolution = entity.GetString("Resolution"),
                    TicketPriority = entity.GetString("TicketPriority"),
                    TicketChannel = entity.GetString("TicketChannel"),
                    FirstResponseTime = entity.GetDateTimeOffset("FirstResponseTime"),
                    TimeToResolution = entity.GetDateTimeOffset("TimeToResolution"),
                    CustomerSatisfactionRating = entity.GetInt32("CustomerSatisfactionRating") ?? 0
                };

                return ticket;
            }

            private static TEnum ParseEnum<TEnum>(string value) where TEnum : struct
            {
                if (string.IsNullOrEmpty(value))
                {
                    throw new ArgumentException($"Value for {typeof(TEnum).Name} cannot be null or empty", nameof(value));
                }

                if (!Enum.TryParse(value, out TEnum result))
                {
                    throw new ArgumentException($"Invalid value for {typeof(TEnum).Name}: {value}", nameof(value));
                }

                return result;
            }
        }
    }





