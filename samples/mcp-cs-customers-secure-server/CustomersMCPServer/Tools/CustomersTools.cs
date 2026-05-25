using System.ComponentModel;
using System.Text.Json;
using ModelContextProtocol.Server;

internal class CustomersTools
{
    private static readonly object SyncRoot = new();
    private static readonly Lazy<List<Customer>> Customers = new(LoadCustomers, isThreadSafe: true);

    private static readonly string DataFilePath =
        Path.Combine(AppContext.BaseDirectory, "data", "customers.json");

    /// <summary>
    /// Returns the current list of customers.
    /// </summary>
    /// <returns>A read-only list of customers.</returns>
    [McpServerTool]
    [Description("Returns the current list of customers.")]
    public IReadOnlyList<Customer> ListCustomers()
    {
        lock (SyncRoot)
        {
            return Customers.Value
                .Select(customer => new Customer
                {
                    Id = customer.Id,
                    CompanyName = customer.CompanyName,
                    Country = customer.Country,
                    WebsiteUrl = customer.WebsiteUrl
                })
                .ToList();
        }
    }

    /// <summary>
    /// Returns a single customer identified by ID.
    /// </summary>
    /// <param name="id">ID of the customer to retrieve.</param>
    /// <returns>The customer with the specified ID.</returns>
    /// <exception cref="InvalidOperationException">Thrown if the customer with the specified ID is not found.</exception>
    [McpServerTool]
    [Description("Returns a single customer identified by ID.")]
    public Customer GetCustomerById(
        [Description("ID of the customer to retrieve.")] Guid id)
    {
        lock (SyncRoot)
        {
            var existingCustomer = Customers.Value.FirstOrDefault(c => c.Id == id);

            if (existingCustomer is null)
            {
                throw new InvalidOperationException($"Customer with ID '{id}' was not found.");
            }

            return new Customer
            {
                Id = existingCustomer.Id,
                CompanyName = existingCustomer.CompanyName,
                Country = existingCustomer.Country,
                WebsiteUrl = existingCustomer.WebsiteUrl
            };
        }
    }

    /// <summary>
    /// Inserts a new customer with the specified company name, country, and website URL.
    /// </summary>
    /// <param name="companyName">Company name of the new customer.</param>
    /// <param name="country">Country of the new customer.</param>
    /// <param name="websiteUrl">Website URL of the new customer.</param>
    /// <returns>The newly created customer.</returns>
    /// <exception cref="InvalidOperationException">Thrown if a customer with the same company name already exists.</exception>
    [McpServerTool]
    [Description("Inserts a new customer.")]
    public Customer InsertCustomer(
        [Description("Company name of the new customer.")] string companyName,
        [Description("Country of the new customer.")] string country,
        [Description("Website URL of the new customer.")] string websiteUrl)
    {
        ValidateCustomerFields(companyName, country, websiteUrl);

        lock (SyncRoot)
        {
            if (Customers.Value.Any(c => c.CompanyName.Equals(companyName, StringComparison.OrdinalIgnoreCase)))
            {
                throw new InvalidOperationException($"A customer with company name '{companyName}' already exists.");
            }

            var customer = new Customer
            {
                Id = Guid.NewGuid(),
                CompanyName = companyName.Trim(),
                Country = country.Trim(),
                WebsiteUrl = websiteUrl.Trim()
            };

            Customers.Value.Add(customer);
            return customer;
        }
    }

    /// <summary>
    /// Updates an existing customer identified by ID with new company name, country, and website URL.
    /// </summary>
    /// <param name="id">ID of the customer to update.</param>
    /// <param name="companyName">New company name.</param>
    /// <param name="country">New country.</param>
    /// <param name="websiteUrl">New website URL.</param>
    /// <returns></returns>
    /// <exception cref="InvalidOperationException"></exception>
    [McpServerTool]
    [Description("Updates an existing customer identified by ID.")]
    public Customer UpdateCustomer(
        [Description("ID of the customer to update.")] Guid id,
        [Description("New company name.")] string companyName,
        [Description("New country.")] string country,
        [Description("New website URL.")] string websiteUrl)
    {
        ValidateCustomerFields(companyName, country, websiteUrl);

        lock (SyncRoot)
        {
            var existingCustomer = Customers.Value.FirstOrDefault(c => c.Id == id);

            if (existingCustomer is null)
            {
                throw new InvalidOperationException($"Customer with ID '{id}' was not found.");
            }

            var companyNameTaken = Customers.Value.Any(c =>
                !ReferenceEquals(c, existingCustomer) &&
                c.CompanyName.Equals(companyName, StringComparison.OrdinalIgnoreCase));

            if (companyNameTaken)
            {
                throw new InvalidOperationException($"A customer with company name '{companyName}' already exists.");
            }

            existingCustomer.CompanyName = companyName.Trim();
            existingCustomer.Country = country.Trim();
            existingCustomer.WebsiteUrl = websiteUrl.Trim();

            return new Customer
            {
                Id = existingCustomer.Id,
                CompanyName = existingCustomer.CompanyName,
                Country = existingCustomer.Country,
                WebsiteUrl = existingCustomer.WebsiteUrl
            };
        }
    }

    /// <summary>
    /// Deletes an existing customer identified by ID.
    /// </summary>
    /// <param name="id">ID of the customer to delete.</param>
    /// <returns>True if the customer was deleted; otherwise, false.</returns>
    [McpServerTool]
    [Description("Deletes an existing customer identified by ID.")]
    public bool DeleteCustomer(
        [Description("ID of the customer to delete.")] Guid id)
    {
        lock (SyncRoot)
        {
            var existingCustomer = Customers.Value.FirstOrDefault(c => c.Id == id);

            if (existingCustomer is null)
            {
                return false;
            }

            return Customers.Value.Remove(existingCustomer);
        }
    }

    /// <summary>
    /// Loads the list of customers from the JSON file. If the file does not exist, returns an empty list.
    /// </summary>
    /// <returns>List of customers.</returns>
    private static List<Customer> LoadCustomers()
    {
        if (!File.Exists(DataFilePath))
        {
            return new List<Customer>();
        }

        var json = File.ReadAllText(DataFilePath);
        var customers = JsonSerializer.Deserialize<List<Customer>>(json) ?? new List<Customer>();

        // Backward compatibility for seed files without IDs.
        var seenIds = new HashSet<Guid>();
        foreach (var customer in customers)
        {
            if (customer.Id == Guid.Empty || !seenIds.Add(customer.Id))
            {
                Guid newId;
                do
                {
                    newId = Guid.NewGuid();
                }
                while (!seenIds.Add(newId));

                customer.Id = newId;
            }
        }

        return customers;
    }

    /// <summary>
    /// Validates the customer fields for insertion and update operations.
    /// </summary>
    /// <param name="companyName">The company name of the customer.</param>
    /// <param name="country">The country of the customer.</param>
    /// <param name="websiteUrl">The website URL of the customer.</param>
    /// <exception cref="ArgumentException">Thrown when any of the customer fields are invalid.</exception>
    private static void ValidateCustomerFields(string companyName, string country, string websiteUrl)
    {
        if (string.IsNullOrWhiteSpace(companyName))
        {
            throw new ArgumentException("Company name is required.", nameof(companyName));
        }

        if (string.IsNullOrWhiteSpace(country))
        {
            throw new ArgumentException("Country is required.", nameof(country));
        }

        if (string.IsNullOrWhiteSpace(websiteUrl))
        {
            throw new ArgumentException("Website URL is required.", nameof(websiteUrl));
        }

        if (!Uri.TryCreate(websiteUrl.Trim(), UriKind.Absolute, out _))
        {
            throw new ArgumentException("Website URL must be a valid absolute URL.", nameof(websiteUrl));
        }
    }

    /// <summary>
    /// Represents a customer with ID, company name, country, and website URL.
    /// </summary>
    public class Customer
    {
        /// <summary>
        /// Gets or sets the unique identifier for the customer.
        /// </summary>
        [Description("Unique customer ID.")]
        public Guid Id { get; set; }

        /// <summary>
        /// Gets or sets the company name of the customer.
        /// </summary>
        [Description("Customer company name.")]
        public string CompanyName { get; set; } = string.Empty;

        /// <summary>
        /// Gets or sets the country of the customer.
        /// </summary>
        [Description("Customer country.")]
        public string Country { get; set; } = string.Empty;

        /// <summary>
        /// Gets or sets the website URL of the customer.
        /// </summary>
        [Description("Customer website URL.")]
        public string WebsiteUrl { get; set; } = string.Empty;
    }
}